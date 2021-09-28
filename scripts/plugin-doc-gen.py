#!/usr/bin/python3

import sys
import json
from os.path import join, dirname, abspath
from pprint import pprint
from mako.template import Template

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary

Glossary.init()

"""
Mako template engine:
	https://docs.makotemplates.org/en/latest/
	https://github.com/sqlalchemy/mako
	https://pypi.org/project/Mako/
	Package python3-mako in Debian repos
"""

template = Template("""
${"##"} ${description} ${"##"}

${"### General Information ###"}
Name | Value
---- | -------
Name | ${name}
snake_case_name | ${lname}
Description | ${description}
Extensions | ${", ".join([codeValue(ext) for ext in extensions])}
Read support | ${yesNo(canRead)}
Write support | ${yesNo(canWrite)}
Single-file | ${yesNo(singleFile)}
Kind | ${kindEmoji(kind)} ${kind}
Wiki | ${wiki_md}
Website | ${website_md}


% if readOptions:
${"### Read options ###"}
Name | Default | Type | Comment
---- | ------- | ---- | -------
% for optName, default in readOptions.items():
`${optName}` | ${codeValue(default)} | ${optionsType[optName]} | ${optionsComment[optName]}
% endfor
% endif

% if writeOptions:
${"### Write options ###"}
Name | Default | Type | Comment
---- | ------- | ---- | -------
% for optName, default in writeOptions.items():
`${optName}` | ${codeValue(default)} | ${optionsType[optName]} | ${optionsComment[optName]}
% endfor
% endif

% if readDependsLinksMD and readDependsLinksMD == writeDependsLinksMD:
${"### Dependencies for reading and writing ###"}
Links: ${readDependsLinksMD}

To install, run:

    ${readDependsCmd}

% else:
	% if readDependsLinksMD:
${"### Dependencies for reading ###"}
Links: ${readDependsLinksMD}

To install, run:

    ${readDependsCmd}

	% endif

	% if writeDependsLinksMD:
${"### Dependencies for writing ###"}
Links: ${writeDependsLinksMD}

To install, run

    ${writeDependsCmd}

	% endif
% endif

% if tools:
${"### Dictionary Applications/Tools ###"}
Name & Website | License | Platforms
-------------- | ------- | ---------
% for tool in tools:
[${tool["name"]}](${tool["web"]}) | ${tool["license"]} | ${", ".join(tool["platforms"])}
% endfor
% endif
""")

indexTemplate = Template("""
Description | Name | Doc Link
----------- | ---- | --------
% for p in plugins:
${p.description} | ${p.name} | [${p.lname}.md](./${p.lname}.md)
% endfor
""")

def codeValue(x):
	s = str(x)
	if s:
		return "`" + s + "`"
	return ""

def yesNo(x):
	if x is True:
		return "Yes"
	if x is False:
		return "No"
	return ""

def kindEmoji(kind):
	if not kind:
		return ""
	return {
		"text": "📝",
		"binary": "🔢",
		"directory": "📁",
		"package": "📦",
	}[kind]

for p in Glossary.plugins.values():
	module = p.pluginModule
	optionsProp = p.optionsProp

	wiki = module.wiki
	wiki_md = "―"
	if wiki:
		if wiki.startswith("https://github.com/"):
			wiki_title = "@" + wiki[len("https://github.com/"):]
		else:
			wiki_title = wiki.split("/")[-1].replace("_", " ")
		wiki_md = f"[{wiki_title}]({wiki})"

	website_md = "―"
	website = module.website
	if website:
		if isinstance(website, str):
			website_md = website
		else:
			try:
				url, title = website
			except ValueError:
				raise ValueError(f"website = {website!r}")
			title = title.replace("|", "\\|")
			website_md = f"[{title}]({url})"

	readDependsLinksMD = ""
	readDependsCmd = ""
	if p.canRead and hasattr(module.Reader, "depends"):
		readDependsLinksMD = ", ".join([
			f"[{pypiName.replace('==', ' ')}](https://pypi.org/project/{pypiName.replace('==', '/')})"
			for pypiName in module.Reader.depends.values()
		])
		readDependsCmd = "pip3 install " + " ".join(
			module.Reader.depends.values()
		)

	writeDependsLinksMD = ""
	writeDependsCmd = ""
	if p.canWrite and hasattr(module.Writer, "depends"):
		writeDependsLinksMD = ", ".join([
			f"[{pypiName}](https://pypi.org/project/{pypiName.replace('==', '/')})"
			for pypiName in module.Writer.depends.values()
		])
		writeDependsCmd = "pip3 install " + " ".join(
			module.Writer.depends.values()
		)

	tools = getattr(module, "tools", [])

	text = template.render(
		codeValue=codeValue,
		yesNo=yesNo,
		kindEmoji=kindEmoji,
		name=p.name,
		lname=p.lname,
		description=p.description,
		extensions=p.extensions,
		canRead=p.canRead,
		canWrite=p.canWrite,
		singleFile=p.singleFile,
		kind=module.kind,
		wiki_md=wiki_md,
		website_md=website_md,
		optionsProp=optionsProp,
		readOptions=p.getReadOptions(),
		writeOptions=p.getWriteOptions(),
		optionsComment={
			optName: opt.comment.replace("\n", "<br />")
			for optName, opt in optionsProp.items()
		},
		optionsType={
			optName: opt.typ
			for optName, opt in optionsProp.items()
		},
		readDependsLinksMD=readDependsLinksMD,
		readDependsCmd=readDependsCmd,
		writeDependsLinksMD=writeDependsLinksMD,
		writeDependsCmd=writeDependsCmd,
		tools=tools,
	)
	with open(join("doc", "p", f"{p.lname}.md"), mode="w") as _file:
		_file.write(text)

indexText = indexTemplate.render(
	plugins=sorted(
		Glossary.plugins.values(),
		key=lambda p: p.description.lower(),
	),
)
with open(join("doc", "p", f"__index__.md"), mode="w") as _file:
	_file.write(indexText)
