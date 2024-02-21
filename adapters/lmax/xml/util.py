import xml


def pretty_xml(value: str):
    return xml.dom.minidom.parseString(value).toprettyxml(indent="\t")


def unpretty_xml(value: str) -> str:
    return value.replace("\n", "").replace("\t", "").replace(" ", "")
