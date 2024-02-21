from pathlib import Path
from xml.etree import ElementTree

from pytower.adapters.lmax.xml.types import LmaxCurrencyPair


class TestTypes:
    def test_currency_pairs(self):
        folder = "/Users/g1/BU/projects/pytower_develop/pytower/adapters/lmax/xml/responses/instruments/currency_pairs"

        for path in Path(folder).rglob("*.xml"):
            root = ElementTree.fromstring(path.read_text())
            for elem in root.findall(".//instrument"):
                LmaxCurrencyPair.from_xml(elem)
