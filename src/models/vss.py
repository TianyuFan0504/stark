import os
import os.path as osp
import torch    
from typing import Any
from src.models.model import ModelForSemiStructQA
from src.tools.api import get_ada_embeddings, get_ada_embedding
from tqdm import tqdm


class VSS(ModelForSemiStructQA):
    
    def __init__(self, 
                 database,
                 query_emb_dir, 
                 candidates_emb_dir):
        '''
        Vector Similarity Search
        Args:
            query_emb_dir (str): directory to query embeddings
            candidates_emb_dir (str): directory to candidate embeddings
            database (src.benchmarks.semistruct.SemiStruct): database
        '''
        
        super(VSS, self).__init__(database)
        self.query_emb_dir = query_emb_dir
        self.candidates_emb_dir = candidates_emb_dir

        candidate_emb_path = osp.join(candidates_emb_dir, 'candidate_emb_dict.pt')
        if osp.exists(candidate_emb_path):
            candidate_emb_dict = torch.load(candidate_emb_path)
            print(f'Loaded candidate_emb_dict from {candidate_emb_path}!')
        else:
            print('Loading candidate embeddings...')
            candidate_emb_dict = {}
            for idx in tqdm(self.candidate_ids):
                candidate_emb_dict[idx] = torch.load(osp.join(candidates_emb_dir, f'{idx}.pt'))
            torch.save(candidate_emb_dict, candidate_emb_path)
            print(f'Saved candidate_emb_dict to {candidate_emb_path}!')

        assert len(candidate_emb_dict) == len(self.candidate_ids)
        candidate_embs = [candidate_emb_dict[idx] for idx in self.candidate_ids]
        self.candidate_embs = torch.cat(candidate_embs, dim=0)

    def forward(self, 
                query: str,
                query_id: int,
                **kwargs: Any):
        
        if query_id is None:
            query_emb = get_ada_embeddings(query)
        else:
            query_emb_path = osp.join(self.query_emb_dir, f'query_{query_id}.pt')
            if os.path.exists(query_emb_path):
                query_emb = torch.load(query_emb_path).view(1, -1)
            else:
                query_emb = get_ada_embedding(query)
                torch.save(query_emb, query_emb_path)
        similarity = torch.matmul(query_emb.cuda(), 
                                  self.candidate_embs.cuda().T).cpu().view(-1)
        pred_dict = {self.candidate_ids[i]: similarity[i] for i in range(len(self.candidate_ids))}
        return pred_dict