'''
Created on Oct 23, 2016

@author: Melvin Laux
'''

import numpy as np

def postprocess(data, doc_start):
    
    for i in xrange(data.shape[0]-1):
        if doc_start[i] and data[i]==0:
            data[i] = 2
        
        if data[i]==1 and data[i+1]==0:
            data[i+1] = 2
    
    return data

def check_document_syntax(document):
    for i in xrange(len(document)-1):
        
        # check for invalid labels
        if document[i] not in [0,1,2]:
            print 'found invalid label', document
            return False
        
        # check for forbidden transitions
        if ((document[i]==1) and (document[i+1]==0)):
            print 'found forbidden transition', document
            return False 
        
    return True


def extract_spans(iob_document, doc_id=0):
    
    positions = np.where(iob_document==2)[0]
    splits = np.split(iob_document, positions)
    
    lengths = map(lambda x: len(x[x != 1]), splits[1:])
    
    indices = np.ones(positions.shape)*doc_id
    
    return np.column_stack((indices, np.array(positions), np.array(lengths)))


def iob_to_span(iob_data, num_docs):
    spans = np.zeros((0,3))
    docs = np.split(iob_data, int(num_docs))
    for j in xrange(len(docs)):
        for i in xrange(iob_data.shape[1]):
            spans = np.append(spans, extract_spans(docs[j][:,i], doc_id=j), 0)
            
    return spans


def span_to_iob(span_data, num_docs, doc_length):
    iob_data = np.ones((doc_length,1)) * 1
    
    for i in xrange(span_data.shape[0]):
        iob_data[int(span_data[i,0])] = 2
        iob_data[int(span_data[i,0]+1):int(span_data[i,0]+1)+int(span_data[i,1])] = 0
        
    return iob_data


def remove_span_overlaps(span_data):
    span_ids = []
    spanwords = []
    
    for i in xrange(span_data.shape[0]):
        words = range(span_data[i,0],span_data[i,1])
        if not set(spanwords).intersection(words):
            span_ids += [i]
            spanwords += words        
            
    return span_data[span_ids, :]
    