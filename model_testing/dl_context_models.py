"""This file contains deep learning models to achieve similar functions as context_based_models.py"""
from t2t_models import text_encoding
from common import constants as const
from common import file_tools as ft
from text_cleaning import example_parsing as ex_parsing

import os
import logging
import pickle


class ContextModel:
    def __init__(self):
        self._docvec_dict = {}

    def infer_vector(self, doc):
        raise NotImplementedError

    def _make_docvec_dict(self, docs):
        raise NotImplementedError


class T2TContextModel(ContextModel):
    @staticmethod
    def make_sure_docs_are_strings(docs):
        doc_type = type(docs[0])
        if doc_type is list or doc_type is tuple:
            str_docs = [' '.join(doc) for doc in docs]

        elif doc_type is str:
            str_docs = docs
        else:
            raise TypeError('doc type should either be list or str or tuple')
        return str_docs

    def __init__(self, load_aaer_data=False, doc_length=10, docs=None):
        """
        Args:
            load_aaer_data: if true, the model will automatically build/save/load docvec_dict with aaer data
            doc_length: used for Ngrams from aaer corpus. default is 10
            docs: not needed if load_aaer_data is True
        """
        super().__init__()
        if load_aaer_data:
            self._load_aaer_data(doc_length)
        else:
            if docs:
                self.update(docs)

    def preferred_doc_length(self):
        key, _ = next(iter(self._docvec_dict))
        return len(key.split(' '))

    def infer_vector(self, doc):
        if type(doc) is list:
            doc = ' '.join(doc)
        try:
            vec = self._docvec_dict[doc]
        except KeyError:
            logging.info('not found in local data. using t2t model to infer...')
            self.update([doc])
            vec = self._docvec_dict[doc]
        return vec

    def infer_vectors_dict(self, docs):
        str_docs = self.make_sure_docs_are_strings(docs)
        # print(str_docs)
        self._make_docvec_dict(str_docs)
        vd = {doc: self._docvec_dict[doc] for doc in str_docs}
        return vd

    def _make_docvec_dict(self, docs):
        str_docs = self.make_sure_docs_are_strings(docs)
        # str_docs[:] = [doc for doc in str_docs and not in self._docvec_dict.keys()]
        set_docs = set(str_docs)
        # keys = set(self._docvec_dict.keys())

        # update only docs not existed in dict
        # set_docs = set_docs - keys
        # logging.info('set_docs:')
        # logging.info(set_docs)
        # logging.info(keys)
        # logging.info(str_docs)

        if len(set_docs) > 0:
            docs_vocab = list(set_docs)
            encoding_model = text_encoding.TextEncoding(docs_vocab)
            encodings = encoding_model.encode(encoding_len=1)

            self._docvec_dict.update(dict(zip(docs_vocab, encodings)))

    def update(self, docs):
        self._make_docvec_dict(docs=docs)

    def _load_aaer_data(self, doc_length):
        # data only contains test files, to save computing & memory costs
        self.save_dir = const.GENERATED_DATA_DIR
        self.dict_save_fname = os.path.join(self.save_dir, "dl_doc_dict_%s_%d.%s" %
                                            (self.__class__.__name__, doc_length, const.PICKLE_FILE_EXTENSION))
        try:
            logging.info("loading saved data from %s" % self.dict_save_fname)
            with open(self.dict_save_fname, 'rb') as f:
                self._docvec_dict = pickle.load(f)
        except FileNotFoundError:
            logging.info("%s not found. Start building...")
            test_files = ft.list_file_paths_under_dir(const.TEST_DIR, ['txt'])
            docs = []
            for test_file in test_files:
                docs += ex_parsing.ngrams_from_file(ft.get_source_file_by_example_file(test_file), n=doc_length)
            # print(docs)
            self._make_docvec_dict(docs)
            logging.info("saving dict to %s" % self.dict_save_fname)
            with open(self.dict_save_fname, 'wb') as f:
                pickle.dump(self._docvec_dict, f)