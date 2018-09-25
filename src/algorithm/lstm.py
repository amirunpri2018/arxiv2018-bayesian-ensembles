import datetime

import numpy as np


class LSTM:

    train_type = 'Bayes'

    def init(self, alpha0_data, N, text, doc_start, nclasses, max_vb_iters, crf_probs):

        self.crf_probs = crf_probs

        self.n_epochs_per_vb_iter = 1#3 # this may be too much?
        self.max_vb_iters = max_vb_iters

        self.probs = None

        self.N = N

        labels = np.zeros(N) # blank at this point. The labels get changed in each VB iteration

        from lample_lstm_tagger.lstm_wrapper import data_to_lstm_format, LSTMWrapper

        self.sentences, self.IOB_map, self.IOB_label = data_to_lstm_format(N, text, doc_start, labels, nclasses)

        timestamp = datetime.datetime.now().strftime('started-%Y-%m-%d-%H-%M-%S')
        self.LSTMWrapper = LSTMWrapper('./models_bac_%s' % timestamp)

        self.Ndocs = self.sentences.shape[0]

        self.train_data_objs = None

        self.nclasses = nclasses

        alpha_data = np.copy(alpha0_data)
        self.alpha0_data = np.copy(alpha0_data)

        return alpha_data

    def fit_predict(self, labels, compute_dev_score=False):

        if self.train_type == 'Bayes':
            labels = np.argmax(labels, axis=1) # uses the mode

            # try sampling the posterior distribution. With enough iterations, this should work, but didn't in our tests with 20 iterations.
            #rvsunif = np.random.rand(labels.shape[0], 1)
            #labels = (rvsunif < np.cumsum(labels, axis=1)).argmax(1)

        l = 0
        labels_by_sen = []
        for s, sen in enumerate(self.sentences):
            sen_labels = []
            labels_by_sen.append(sen_labels)
            for t, tok in enumerate(sen):
                self.sentences[s][t][1] = self.IOB_label[labels[l]]
                sen_labels.append(self.IOB_label[labels[l]])
                l += 1

        if self.LSTMWrapper.model is None:
            # the first update needs more epochs to reach a useful level
            n_epochs = self.n_epochs_per_vb_iter + 2

            # don't need to use an dev set here for early stopping as this may break EM
            self.lstm, self.f_eval = self.LSTMWrapper.train_LSTM(self.all_sentences, self.sentences, [], [],
                                                                 self.IOB_map, self.IOB_label,
                                                                 self.nclasses, n_epochs, freq_eval=n_epochs,
                                                                 crf_probs=self.crf_probs,
                                                                 max_niter_no_imprv=2)
        else:
            n_epochs = self.n_epochs_per_vb_iter  # for each bac iteration after the first

            best_dev = -np.inf
            last_score = best_dev
            niter_no_imprv = 0

            self.LSTMWrapper.model.best_model_saved = False

            for epoch in range(n_epochs):
                niter_no_imprv, best_dev, last_score = self.LSTMWrapper.run_epoch(0, niter_no_imprv,
                                    best_dev, last_score, compute_dev_score and (((epoch+1) % freq_eval) == 0) and (epoch < n_epochs))

        # now make predictions for all sentences
        if self.probs is None:
            agg, self.probs = self.LSTMWrapper.predict_LSTM(self.sentences)

            print('LSTM assigned class labels %s' % str(np.unique(agg)) )

        return self.probs

    def predict(self, doc_start, text):
        from lample_lstm_tagger.lstm_wrapper import data_to_lstm_format
        N = len(doc_start)
        test_sentences, _, _ = data_to_lstm_format(N, text, doc_start, np.ones(N), self.nclasses)

        # now make predictions for all sentences
        agg, probs = self.LSTMWrapper.predict_LSTM(test_sentences)

        print('LSTM assigned class labels %s' % str(np.unique(agg)))

        return probs

    def log_likelihood(self, C_data, E_t):
        '''
        '''
        lnp_Cdata = C_data * np.log(E_t)
        lnp_Cdata[E_t == 0] = 0
        return np.sum(lnp_Cdata)