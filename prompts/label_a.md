# Labelling instructions — variant A (definitions first)

You label research-paper abstracts. Use only the title and abstract given. Do not use outside knowledge
about the paper, its authors or its venue. When the text does not say, answer `not_stated` (or
`none_stated` / `none` where that is the listed value). Never invent a value: every answer must be copied
exactly from the value lists in `schema/axes.json`.

## Step 1 — relevance gate: `is_ai_hardware`

- `yes`: the paper's contribution is hardware, a hardware architecture, a circuit, a memory/compute
  macro, or hardware-aware mapping/compilation/design-space exploration **for running or training
  machine-learning or neural-network workloads**. In-memory / near-memory computing hardware counts when
  the stated use includes neural networks, AI inference or training, or general matrix/vector kernels
  aimed at them.
- `no`: anything else. Then give `gate_reason_if_no`:
  `ai_for_eda` (machine learning used as a tool to do placement, routing, verification, test, design
  automation), `ai_algorithm_only` (a model or training method with no hardware contribution),
  `security_or_test_of_ai` (attacks, defences, fault testing where the hardware is not the contribution),
  `not_ai` (hardware or memory work with no machine-learning workload, e.g. a pure storage, logic-in-memory,
  database or cryptography paper), `other`.
- `borderline`: you cannot decide from the text. Label all axes anyway.

If the answer is `no`, output only `id`, `is_ai_hardware`, `gate_reason_if_no` and stop for that paper.

## Step 2 — axes (one value each unless stated)

**A0_workload** — the workload the paper targets or evaluates on. `cnn`; `transformer_encoder_vit`
(BERT-like encoders, vision transformers, attention without autoregressive generation);
`llm_autoregressive` (large language models, token-by-token decoding, KV cache); `gnn`; `snn` (spiking);
`rnn_lstm`; `recommendation`; `generative_diffusion`; `training` (the contribution is about training or
on-device learning, whatever the model); `non_nn` (the hardware targets something that is not a neural
network); `generic_dnn` (says "DNN"/"neural network"/"AI" without naming a family, or names MLPs only);
`not_stated`; `other`. If several are named, choose the one the headline result is reported on.

**A1_paradigm** — how the computation is physically carried out.
`digital_spatial_asic` (a conventional digital accelerator: PE arrays, MAC units, custom datapaths);
`systolic_matrix_engine` (explicitly a systolic array or matrix-multiply engine);
`vector_simd_isa_ext` (vector/SIMD units or instruction-set extensions of a programmable core, including RISC-V);
`cgra_dataflow` (coarse-grained reconfigurable or explicit dataflow architectures);
`gpu_simt`; `fpga` (the design is an FPGA implementation or overlay as its target, not just a prototype);
`cim_analog_sram` (in-memory computing in SRAM with analog/charge/current-domain summation);
`cim_analog_nvm` (in-memory computing in a non-volatile array: RRAM, PCM, FeFET, MRAM, flash, memristor crossbars);
`cim_digital` (in-memory computing where the arithmetic is fully digital: digital adder trees, bit-wise logic in the array);
`pim_dram_near_memory` (processing in or next to DRAM/HBM, near-memory accelerators);
`photonic`; `neuromorphic` (spiking/event-driven hardware); `stochastic_or_approximate`;
`target_generic` (a tool, compiler, mapper or methodology with no paradigm of its own);
`not_stated`; `other`.
For in-memory papers that do not say whether the summation is analog or digital, choose by the memory:
non-volatile → `cim_analog_nvm`; SRAM with no statement → `cim_analog_sram` only if analog sensing/ADCs
are mentioned, else `other` is wrong — use `not_stated`.

**A1_device** — the memory device the compute happens in or next to: `sram`, `rram`, `pcm`, `fefet`,
`mram`, `dram`, `flash`, `gain_cell`, `other`; `none` when the paradigm involves no memory-device choice;
`not_stated` when an in-memory paper does not name the device.

**A2_data_residency** — where the operands live and how they reach the compute, as far as the abstract
says: `cache_hierarchy`; `scratchpad_dma` (software-managed local memory filled by DMA or explicit
copies); `shared_l1_cluster` (several cores/engines sharing one local memory); `noc_mesh_tiles` (tiles or
nodes on an on-chip network); `stacked_3d`; `chiplet_multi_die`; `hbm_or_dram_bound` (the design is
organised around off-chip/main-memory bandwidth); `in_array_weights` (weights stay in the compute array);
`not_stated`; `other`.

**A3_numerics** — the number format computed in: `fp32`, `fp16_bf16`, `fp8`, `int8`, `int4_or_less`
(2–4 bit), `binary_ternary`, `mixed_or_variable` (several precisions or run-time variable),
`block_microscaling`, `bit_serial`, `posit_or_lns`, `analog_levels` (multi-level cell conductances with
no digital format stated), `not_stated`, `other`.

**A4_sparsity_codesign** — algorithm-side cooperation the paper relies on: `none_stated`,
`unstructured_sparsity`, `structured_sparsity`, `pruning_hw_codesign`, `quantization_aware` (training or
calibration adapted to the hardware's precision or non-idealities), `token_or_attention_sparsity`,
`nas_hw_codesign`, `other`.

**A5_programmability** — how software reaches the hardware: `isa_extension`;
`tightly_coupled_coprocessor`; `memory_mapped_shared_l1_engine` (a register-programmed engine that reads
and writes a memory shared with the cores); `standalone_accelerator`; `host_offload` (a device behind
PCIe/USB/network or a host CPU that ships work to it); `fixed_function`; `not_stated`; `other`.

**A6_eval_rung** — the most concrete evidence the abstract reports for its headline result:
`analytical` (equations, models); `simulator` (architecture/circuit simulation, SPICE, behavioural or
framework-level simulation); `rtl_sim`; `fpga`; `post_synthesis`; `post_layout`; `silicon` (fabricated
chip measured); `board_or_system` (a measured deployed system); `not_stated`. Words such as "fabricated",
"measured", "taped out", "prototype chip" mean `silicon`; "synthesized in 28 nm" means `post_synthesis`;
"placed and routed"/"layout" means `post_layout`.

**A6_baseline_class** — what the headline number is compared against: `cpu`, `gpu`,
`prior_accelerator` (a named or "state-of-the-art" earlier design), `own_variant_only` (only against the
authors' own baseline configuration), `none_stated`.

**A7_scale** — the size of the thing designed: `macro_circuit` (a cell, array, ADC, memory macro);
`engine_core` (one accelerator engine or core); `cluster_tile` (several engines/cores sharing local
memory, or one tile); `soc_chip` (a whole chip with host, memory and peripherals); `multi_chip_chiplet`;
`system_datacenter`; `tool_only` (software, flow or methodology); `not_stated`.

**design_method** — how the hardware description was produced, if stated: `hand_rtl`, `hls`,
`generator` (parameterised generator or template framework), `ai_generated`, `not_stated`.

**lever** — a list of one to three things the contribution acts on, most important first:
`dataflow_tiling_buffering`, `precision_format`, `sparsity`, `mapping_dse_compiler`,
`interconnect_noc_chiplet`, `memory_hierarchy`, `nonideality_reliability` (device variation, noise,
drift, faults, IR drop, endurance), `programmability_sw_stack`, `on_device_training`, `security`,
`power_thermal`, `circuit_macro_design`, `scheduling_control`, `other`.

## Output

One JSON object per paper, one per line, keys exactly as above plus `id`. No commentary, no markdown.
