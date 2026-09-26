import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"demo"))
import unittest
import torch
from transformers import GemmaConfig,SiglipVisionConfig
from transformers.models.gemma.modeling_gemma import GemmaRotaryEmbedding
from transformers.models.siglip.modeling_siglip import SiglipVisionEmbeddings
from load_helpers import restore_nonpersistent_buffers

class BufferRestoreTests(unittest.TestCase):
    def test_rotary_matches_regular_upstream_constructor(self):
        cfg=GemmaConfig(hidden_size=64,num_attention_heads=4,head_dim=16)
        reference=GemmaRotaryEmbedding(cfg,device="cpu")
        with torch.device("meta"):delayed=GemmaRotaryEmbedding(cfg)
        restore_nonpersistent_buffers(delayed)
        torch.testing.assert_close(delayed.inv_freq,reference.inv_freq)
        self.assertIs(delayed.original_inv_freq,delayed.inv_freq)
    def test_positions_match_and_parameters_stay_uninitialized(self):
        cfg=SiglipVisionConfig(image_size=32,patch_size=8,hidden_size=16)
        reference=SiglipVisionEmbeddings(cfg)
        with torch.device("meta"):delayed=SiglipVisionEmbeddings(cfg)
        restore_nonpersistent_buffers(delayed)
        torch.testing.assert_close(delayed.position_ids,reference.position_ids)
        self.assertTrue(all(p.is_meta for p in delayed.parameters()))
    def test_unknown_missing_buffer_is_rejected(self):
        module=torch.nn.Module();module.register_buffer("unknown",torch.empty(2,device="meta"))
        with self.assertRaises(RuntimeError):restore_nonpersistent_buffers(module)
if __name__=="__main__":unittest.main()
