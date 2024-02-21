import xml.dom.minidom
import xml.sax


class LMAXSaxHandlerDebug(xml.sax.ContentHandler):
    def __init__(self):
        self._value = ""

    def startElement(self, name, attrs):
        print(f"<{name}>")

    def endElement(self, name):
        print(self._value)
        print(f"</{name}>")
        self._value = ""

    def characters(self, c):
        self._value += c

    def get_result(self) -> str | None:
        return None


class LMAXSaxHandler(xml.sax.ContentHandler):
    def __init__(self, target_element: str | None = None):
        self._value = ""
        self._target_element = target_element
        self._data: list[str] = []
        self._result = None

        self._is_capturing = False

    def get_result(self) -> str | None:
        return self._result

    def startElement(self, name, attrs):
        self._current_element = name
        self._start = f"<{name}>"
        # print(start)
        if not self._is_capturing and self._target_element == self._current_element:
            self._is_capturing = True

        if self._is_capturing:
            self._data.append(self._start)

    def endElement(self, name):
        self._end = f"</{name}>"

        if self._is_capturing:
            if self._value != "":
                self._data.append(self._value)
            self._data.append(self._end)

        # self.debug()

        if name == self._target_element:
            self._result = xml.dom.minidom.parseString("".join(self._data)).toprettyxml(indent="\t")
            self._data = []
            self._is_capturing = False

        self._value = ""

    def characters(self, c):
        self._value += c

    def ignorableWhitespace(self):
        pass

    def debug(self):
        print(self._start)
        if self._value != "":
            print(self._value)
        print(self._end)


# import xml.sax
# import xml.dom.minidom
# from typing import Callable
# class LMAXSaxHandler(xml.sax.ContentHandler):
#     def __init__(self, target_element: str = None):

#         self.is_complete = False
#         self.result = None

#         self._target_element = target_element

#         self._data = []
#         self._value = ""
#         self._current_element = None

#     def startElement(self, name, attrs):
#         self._current_element = name

#         if self._is_capturing:
#             self._data.append(f"<{name}>")

#     def endElement(self, name):


#         if self._is_capturing:
#             self._data.append(self._value)
#             self._value = ""
#             self._data.append(f"</{name}>")

#         if name == self._target_element:

#             self.is_complete = True
#             self._data = []


#     def characters(self, c):
#         self._value += c

#     @property
#     def _is_capturing(self) -> bool:
#         if self._target_element is None:
#             return True
#         return self._target_element == self._current_element
