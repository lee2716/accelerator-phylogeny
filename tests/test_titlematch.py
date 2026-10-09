"""Run: python3 tests/test_titlematch.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from titlematch import TitleIndex

index = TitleIndex({"date18": "ReRAM-based accelerator for deep learning",
                    "fault": "Fault Tolerance in Neuromorphic Computing Systems",
                    "short": "RRAM Accelerator",
                    "macro": "A Digital In-Memory Computing Macro for Edge Inference"})
# the incident: a longer title that contains a known title must not match it
assert index.find('L. Song et al., "PipeLayer: A pipelined ReRAM-based accelerator for deep learning," in HPCA, 2017.') == set()
assert index.find("PipeLayer: A Pipelined ReRAM-Based Accelerator for Deep Learning") == set()
# the genuine citation still matches, in the common reference styles
assert index.find('[7] B. Li et al., "ReRAM-based accelerator for deep learning," in DATE, 2018, pp. 815-820.') == {"date18"}
assert index.find("B. Li, L. Song, F. Chen. 2018. ReRAM-based accelerator for deep learning. In DATE. 815–820.") == {"date18"}
assert index.find("ReRAM-based accelerator for deep learning") == {"date18"}                     # Crossref article-title field
assert index.find('M. Liu et al. "Fault tolerance in neuro-\nmorphic computing systems," ASP-DAC 2019') == {"fault"}   # hyphenated line break
# a known title followed by more title words is a different paper
assert index.find('X. Li, "A Digital In-Memory Computing Macro for Edge Inference with Sparsity," DATE 2023') == set()
assert index.find("X. Li. A Digital In-Memory Computing Macro for Edge Inference. DAC 2022") == {"macro"}
assert index.find("RRAM accelerator, 2018") == set()                                               # too short to match safely
assert index.find("") == set()
print("test_titlematch: 10 checks passed")
