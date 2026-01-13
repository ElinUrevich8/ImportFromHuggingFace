import re

pattern = r"\d+"
text = " There are 123 apples and 456 oranges."

match = re.search(pattern, text)
print(f"Match: {match.group()}")
print(f"Span: {match.span()}")



matches = re.findall(pattern, text)
print(matches)
# To execute this code in VS Code, you can use the shortcut:
# Windows/Linux: Ctrl + F5
# macOS: Control + F5
# Or, if you have the 'Code Runner' extension installed: Ctrl + Alt + N
