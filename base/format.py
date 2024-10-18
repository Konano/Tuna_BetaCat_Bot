import re


def escaped(str):  # MarkdownV2 Mode
    return re.sub(r'([\_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])', '\\\\\\1', str)
