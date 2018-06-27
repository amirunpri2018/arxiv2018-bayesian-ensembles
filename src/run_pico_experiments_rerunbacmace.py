'''
Created on April 27, 2018

@author: Edwin Simpson
'''

from evaluation.experiment import Experiment
import data.load_data as load_data
import numpy as np

output_dir = '../../data/bayesian_annotator_combination/output/bio_task1/'

regen_data = False
gt, annos, doc_start, text, gt_task1_dev, gt_dev, doc_start_dev, text_dev = \
    load_data.load_biomedical_data(regen_data)

exp = Experiment(None, 3, annos.shape[1], None, max_iter=20)

exp.save_results = True
exp.opt_hyper = False #True

exp.alpha0_diags = 100
exp.alpha0_factor = 9

best_bac_wm = 'bac_seq' # choose model with best score for the different BAC worker models
best_nu0factor = 0.1
best_diags = 0.1
best_factor = 0.1

nu_factors = [0.1]#, 1, 10, 100]
diags = [0.1, 1, 10]#, 100] #, 50, 100]#[1, 50, 100]#[1, 5, 10, 50]
factors = [0.1, 1, 10]
methods_to_tune = [
                   'bac_mace_integrateBOF'
                   ]

best_bac_wm_score = -np.inf

# tune with small dataset to save time
idxs = np.argwhere(gt_task1_dev != -1)[:, 0]
idxs = np.concatenate((idxs, np.argwhere(gt != -1)[:, 0]))
idxs = np.concatenate((idxs, np.argwhere((gt == -1) & (gt_task1_dev == -1))[:300, 0]))  # 100 more to make sure the dataset is reasonable size

tune_gt_dev = gt_task1_dev[idxs]
tune_annos = annos[idxs]
tune_doc_start = doc_start[idxs]
tune_text = text[idxs]

for m, method in enumerate(methods_to_tune):
    print('TUNING %s' % method)

    best_scores = exp.tune_alpha0(diags, factors, nu_factors, method, tune_annos, tune_gt_dev, tune_doc_start,
                                  output_dir, tune_text, metric_idx_to_optimise=11)
    best_idxs = best_scores[1:].astype(int)
    exp.nu0_factor = nu_factors[best_idxs[0]]
    exp.alpha0_diags = diags[best_idxs[1]]
    exp.alpha0_factor = factors[best_idxs[2]]

    print('Best values: %f, %f' % (exp.alpha0_diags, exp.alpha0_factor))

    # this will run task 1 -- train on all crowdsourced data, test on the labelled portion thereof
    exp.methods = [method]
    exp.run_methods(annos, gt, doc_start, output_dir, text, rerun_all=True, return_model=True,
                ground_truth_val=gt_dev, doc_start_val=doc_start_dev, text_val=text_dev,
                new_data=regen_data
    )

    best_score = np.max(best_scores)
    if 'bac' in method and best_score > best_bac_wm_score:
        best_bac_wm = method
        best_bac_wm_score = best_score
        best_diags = exp.alpha0_diags
        best_factor = exp.alpha0_factor
        best_nu0factor = exp.nu0_factor