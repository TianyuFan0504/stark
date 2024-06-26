import torch.nn as nn
from typing import Any, Union
import torch
from torchmetrics.functional.retrieval import retrieval_hit_rate, \
                                              retrieval_reciprocal_rank, \
                                              retrieval_recall, retrieval_precision, \
                                              retrieval_average_precision, \
                                              retrieval_normalized_dcg, \
                                              retrieval_r_precision



class ModelForSemiStructQA(nn.Module):
    
    def __init__(self, database):
        super(ModelForSemiStructQA, self).__init__()
        self.database = database
        self.candidate_ids = database.candidate_ids
        self.num_candidates = database.num_candidates
    
    def forward(self, 
                query: Union[str, list], 
                candidates=None,
                query_id=None,
                **kwargs: Any):
        '''
        Args:
            query (Union[str, list]): query string or a list of query strings
            candidates (Union[list, None]): a list of candidate ids (optional)
            query_idx (Union[int, list, None]): query index (optional)
            
        Returns:
            pred_answer (Union[str, int, list]): predicted answer or a list of answer strings
        '''
        raise NotImplementedError
    
    def evaluate(self, 
                 pred_dict: dict, 
                 answer_ids: torch.LongTensor, 
                 metrics=['mrr', 'hit@3', 'recall@20'], 
                 **kwargs: Any):
        '''
        Args:
            pred_dict (torch.Tensor): predicted answer ids or scores
            answer_ids (torch.LongTensor): ground truth answer ids
            metrics (list): a list of metrics to be evaluated, 
                including 'mrr', 'hit@k', 'recall@k', 'precision@k', 'map@k', 'ndcg@k'
        Returns:
            eval_metrics (dict): a dictionary of evaluation metrics
        '''
        pred_ids = torch.LongTensor(list(pred_dict.keys())).view(-1)
        pred = torch.FloatTensor(list(pred_dict.values())).view(-1)
        answer_ids = answer_ids.view(-1)

        all_pred = torch.ones(max(self.candidate_ids) + 1, dtype=torch.float) * min(pred) - 1
        all_pred[pred_ids] = pred
        all_pred = all_pred[self.candidate_ids]

        bool_gd = torch.zeros(max(self.candidate_ids) + 1, dtype=torch.bool)
        bool_gd[answer_ids] = True
        bool_gd = bool_gd[self.candidate_ids]

        eval_metrics = {}
        for metric in metrics:
            k = int(metric.split('@')[-1]) if '@' in metric else None
            if 'mrr' == metric:
                result = retrieval_reciprocal_rank(all_pred, bool_gd)
            elif 'rprecision' == metric:
                result = retrieval_r_precision(all_pred, bool_gd)
            elif 'hit' in metric:
                result = retrieval_hit_rate(all_pred, bool_gd, top_k=k)
            elif 'recall' in metric:
                result = retrieval_recall(all_pred, bool_gd, top_k=k)
            elif 'precision' in metric:
                result = retrieval_precision(all_pred, bool_gd, top_k=k)
            elif 'map' in metric:
                result = retrieval_average_precision(all_pred, bool_gd, top_k=k)
            elif 'ndcg' in metric:
                result = retrieval_normalized_dcg(all_pred, bool_gd, top_k=k)
            eval_metrics[metric] = float(result)

        return eval_metrics