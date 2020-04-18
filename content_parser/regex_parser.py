import os
import re


def get_item(paragraphs, regex):
    for paragraph in paragraphs:
        group = 1
        pattern = re.compile(regex, re.UNICODE | re.IGNORECASE)
        results = [match.group(group) for match in pattern.finditer(paragraph)]
        if(results):
            return results[0]    
    return None
    