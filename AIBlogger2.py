#!/usr/bin/python
# -*- coding: utf-8 -*-

import concurrent.futures
import pprint
import urllib
from asyncio import ALL_COMPLETED
from concurrent.futures.thread import ThreadPoolExecutor

from python.ZestorHelper import ZestorHelper

# temp class to return writing results
class futureReturn:
    section = ''
    writingText = ''

# method which will be called on individual threads simultaneously
def WriteSection(expert, topic, section):
    # Write section 
    writing_prompt = ZestorHelper.open_file('PromptTemplates/openai/prompt_writing.txt').replace('<<EXPERT>>',expert).replace('<<TOPIC>>', TOPIC).replace('<<SECTION>>', section)
    writingText = ZestorHelper.call_ai_engine(ZestorHelper.AI_ENGINE_OPENAI,writing_prompt)
    print('\n\n%s WRITING:%s' % (section,writingText))
    # store writing
    retval = futureReturn()
    retval.section = section
    retval.writingText = writingText
    return retval

# Main program
if __name__ == '__main__':
    
    blogJson = {} # dict for writing results

    inputText = ZestorHelper.open_file('request.txt')
    inputArray = inputText.splitlines()

    EXPERT = inputArray[0] # first line is expert persona
    TOPIC = inputArray[1] # second line is request

    sections_prompt = ZestorHelper.open_file('PromptTemplates/openai/prompt_sections.txt').replace('<<EXPERT>>',EXPERT).replace('<<TOPIC>>',TOPIC)
    sectionsText = ZestorHelper.call_ai_engine(ZestorHelper.AI_ENGINE_OPENAI,sections_prompt)
    sectionsText = ZestorHelper.cleanup_aiengine_output(sectionsText)
    print('\n\nSECTIONS:', sectionsText)

    ZestorHelper.save_file('blog.txt')

    # MULTIPLE SIMULTANEOUS CONCURRENT CALLS TO AI ENGINE
    sectionsArray = sectionsText.splitlines()
    prompt_queue = []
    with ThreadPoolExecutor(max_workers=len(sectionsArray)) as executor:
        ordinal = 1
        for section in sectionsArray:
            prompt_queue.append(executor.submit(WriteSection, EXPERT, TOPIC, section))
            ordinal += 1

    # WAIT FOR ALL SIMULTANEOUS CONCURRENT CALLS TO COMPLETE
    done, not_done = concurrent.futures.wait(prompt_queue,timeout=None,return_when=ALL_COMPLETED)

    for future in prompt_queue:
        try:
            funReturn = future.result()
            blogJson[urllib.parse.quote_plus(funReturn.section.strip())]=funReturn.writingText
        except Exception as exc:
                print('\n\ngenerated an exception: %s' % (exc))

    print('\n\n+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=')
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(blogJson)
    print('\n\n+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=')

    for section in sectionsArray:
        print('Getting "%s"' % (section))
        writingText=blogJson[urllib.parse.quote_plus(section.strip())]
        ZestorHelper.save_file('blog.txt',  writingText + '\r\n', 'a') # append
