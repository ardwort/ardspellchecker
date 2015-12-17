#!/usr/bin/env python

import os
import random
import pprint
import time
import re
import sys

class ILStemmer(object):
    def __init__(self):
        self.OPTION = {
        	'SORT_INSTANCE'	: False, #sort by number of instances
        	'NO_NO_MATCH'	: False, #hide no match entry
        	'NO_DIGIT_ONLY'	: True,  #hide digit only
        	'STRICT_CONFIX'	: False, #use strict disallowed_confixes RULES
        }


        fp  = open('./kamus.txt')
        dic = fp.readlines()
        fp.close()
        self.dicti = {}
        for i in dic:
            attrib = i.lower().split('\t')
            key    = attrib[1].replace(' ','').rstrip(' \t\n\r')
            self.dicti[key] = { 'class': attrib[0], 'lemma': attrib[1].rstrip(' \t\n\r')}

        # Define RULES
        self.VOWEL = 'a|i|u|e|o' #vowels
        self.CONSONANT = 'b|c|d|f|g|h|j|k|l|m|n|p|q|r|s|t|v|w|x|y|z' #consonants
        self.ANY = self.VOWEL + '|' + self.CONSONANT #any characters

        self.RULES = {
            'affixes': (  
                (1,('kah','lah', 'tah', 'pun')),
                (1,('mu','ku', 'nya')),
                (0,('ku','kau')),
                (1,('i','kan', 'an'))
                ),
            'prefixes': (  
        		[0, "(di|ke|se)("+self.ANY+")(.+)", ""], # 0
        		[0, "(ber|ter)("+self.ANY+")(.+)", ""], # 1, 6 normal
        		[0, "(be|te)(r)("+self.VOWEL+")(.+)", ""], # 1, 6 be-rambut
        		[0, "(be|te)("+self.CONSONANT+")({"+self.ANY+"}?)(er)(.+)", ""], # 3, 7 te-bersit, te-percaya
        		[0, "(bel|pel)(ajar|unjur)", ""], # ajar, unjur
        		[0, "(me|pe)(l|m|n|r|w|y)(.+)", ""], # 10, 20: merawat, pemain
        		[0, "(mem|pem)(b|f|v)(.+)", ""], # 11 23: membuat, pembuat
        		[0, "(men|pen)(c|d|j|z)(.+)", ""], # 14 27: mencabut, pencabut
        		[0, "(meng|peng)(g|h|q|x)(.+)", ""], # 16 29: menggiring, penghasut
        		[0, "(meng|peng)("+self.VOWEL+")(.+)", ""], # 17 30 meng-anjurkan, peng-anjur
        		[0, "(mem|pem)("+self.VOWEL+")(.+)", "p"], # 13 26: memerkosa, pemerkosa
        		[0, "(men|pen)("+self.VOWEL+")(.+)", "t"], # 15 28 menutup, penutup
        		[0, "(meng|peng)("+self.VOWEL+")(.+)", "k"], # 17 30 mengalikan, pengali
        		[0, "(meny|peny)("+self.VOWEL+")(.+)", "s"], # 18 31 menyucikan, penyucian
        		[0, "(mem)(p)("+self.CONSONANT+")(.+)", ""], # memproklamasikan
        		[0, "(pem)("+self.CONSONANT+")(.+)", "p"], # pemrogram
        		[0, "(men|pen)(t)("+self.CONSONANT+")(.+)", ""], # mentransmisikan pentransmisian
        		[0, "(meng|peng)(k)("+self.CONSONANT+")(.+)", ""], # mengkristalkan pengkristalan
        		[0, "(men|pen)(s)("+self.CONSONANT+")(.+)", ""], # mensyaratkan pensyaratan
        		[0, "(menge|penge)("+self.CONSONANT+")(.+)", ""], # swarabakti: mengepel
        		[0, "(mempe)(r)("+self.VOWEL+")(.+)", ""], # 21
        		[0, "(memper)("+self.ANY+")(.+)", ""], # 21
        		[0, "(pe)("+self.ANY+")(.+)", ""], # 20
        		[0, "(per)("+self.ANY+")(.+)", ""], # 21
        		[0, "(pel)("+self.CONSONANT+")(.+)", ""], # 32 pelbagai, other?
        		[0, "(mem)(punya)", ""], # Exception: mempunya
        		[0, "(pen)(yair)", "s"], # Exception: penyair > syair
                ),
            	'disallowed_confixes' : (
            		('ber-', '-i'),
            		('ke-', '-i'),
            		('pe-', '-kan'),
            		('di-', '-an'),
            		('meng-', '-an'),
            		('ter-', '-an'),
            		('ku-', '-an'),
            	),
            	'allomorphs' : (
            		{'be' : ('be-', 'ber-', 'bel-')},
            		{'te' : ('te-', 'ter-', 'tel-')},
            		{'pe' : ('pe-', 'per-', 'pel-', 'pen-', 'pem-', 'peng-', 'peny-', 'penge-')},
            		{'me' : ('me-', 'men-', 'mem-', 'meng-', 'meny-', 'menge-')},
            	),
        }

    def cnom(self, pattern, thestring):
        # count non overlapping matches
        return re.subn(pattern, '', thestring)[1]
  
  
    def stem(self, query):
        words = {}
        instance = {}
        paw   = re.compile(r'\W+')
        raw   = paw.split(query)
   
        for r in raw:
            if self.OPTION['NO_DIGIT_ONLY'] and re.search('^\d',r):
                continue
            key = r.lower()
            words[key]= { 'count': self.cnom(key,query)}
            
        for k,v in words.items():
            if k in self.dicti.keys():
                words[k]['roots'] = {}
                words[k]['roots'][k] = {}
                words[k]['roots'][k]['lemma'] = k
            else:
                words[k]['roots'] = self.stem_word(k)
                if len(words[k]['roots']) == 0 and self.OPTION['NO_NO_MATCH']:
                    del words[k]
                    continue
            instance[k] = v['count']
        word_count = len(words)
        if self.OPTION['SORT_INSTANCE']:
            keys = words.keys()
            sorted(instance)
            sorted(keys)
            sorted(words)
        else:
            words = self.ksort(words)
        
        #return words
        #presenting the roots 
        stemmed = ''
        for i in range(len(words)):
            result = words[i][1]['roots']
            for key in result.keys():
                if 'prefixes' in result[key].keys():
                    stemmed += str(result[key]['prefixes'])
                stemmed += str(result[key]['lemma'])
                if 'suffixes' in result[key].keys():
                    stemmed += str(result[key]['suffixes'])
                stemmed += ' '
                
        return stemmed.rstrip()
        

    def ksort(self, data):
         return [(key,data[key]) for key in sorted(data.keys(), reverse=True)]
     
    def stem_word(self, word):
        word = word.strip()
        roots = { word : {}}
        
        #check the word in dictionary (kamus.txt)
        
        if word in self.dicti.keys():
            roots[word]['affixes'] = {} 
        else:
            roots[word]['affixes'] = ''
        
        #if the word contain dash (-)
        
        dash_parts = word.split('-')
        if len(dash_parts) > 1:
            for dash_part in dash_parts:
                roots[dash_part]['affixes'] = {}
        
        #check affixes rules        
        for group in self.RULES['affixes']:
            is_suffix = group[0]
            affixes   = group[1]
            for affix in affixes:
                if is_suffix:
                    pattern = "(.+)("+affix+")"
                else:
                    pattern = "("+affix+")(.+)"
                self.add_root(roots, [is_suffix, pattern, ''])
                
        #check prefixes rules
        for i in range(3):
            for rule in self.RULES['prefixes']:
                self.add_root(roots, rule)
        
        #compiling the output        
        for lemma, attrib in roots.items():
            if lemma not in self.dicti.keys():
                del roots[lemma] #delete arrays if it's not in the dictionary
                continue
            if self.OPTION['STRICT_CONFIX']:
                continue;
            affixes = attrib['affixes']
            for pair in self.RULES['disallowed_confixes']:
                prefix = pair[0]
                suffix = pair[1]
                prefix_key = prefix[:2]
                if prefix_key in self.RULES['allomorphs']:
                    for allomorf in self.RULES['allomorphs'][prefix_key]:
                        if allomorf in affixes and suffix in affixes:
                            del roots[lemma]
                else:
                    if prefix in affixes and suffix in affixes:
                        del roots[lemma]
        for lemma,attrib in roots.items():
            affixes = attrib['affixes']
            attrib['lemma'] = self.dicti[lemma]['lemma']
            attrib['class'] = self.dicti[lemma]['class']
            for affix in attrib['affixes']:
                if affix[:1] == '-':
                    tipe = 'suffixes'
                else:
                    tipe = 'prefixes'
                attrib[tipe] = affix
            try:
                if len(attrib['suffixes']) > 1:
                    ksort(attrib['suffixes'])
            except:
                pass
            roots[lemma] = attrib
        return roots

    def add_root(self, roots, rule):
        is_suffix = rule[0]
        pattern = '^' + rule[1]
        variant = rule[2]
        is_array = lambda var: isinstance(var, (list, tuple))
        for lemma, attrib in roots.items():
            matches = re.findall(pattern,lemma)
            if len(matches) > 0:
                new_lemma = ''
                new_affix = ''
                affix_index = 1 if is_suffix else 0
                for i in range(len(matches[0])):
                    if i != affix_index: new_lemma += matches[0][i]
                if variant: 
                    new_lemma = variant + new_lemma
            
                new_affix += '-' if is_suffix else ''
                new_affix += matches[0][affix_index]+''
            
                new_affix += '' if is_suffix else '-'
                new_affix = new_affix.split()
                if is_array(attrib['affixes']):
                    new_affix = attrib['affixes'] + new_affix
                roots[new_lemma] = { 'affixes': new_affix}
                        
