# Labelling instructions — variant B (questions)

Read each title and abstract and answer the questions below from that text alone. If the text gives no
answer, say so with the listed "no answer" value; never guess from what such papers usually do. Every
answer must be one of the exact strings listed under the same key in `schema/axes.json`.

**Q0 `is_ai_hardware` — Is the thing this paper contributes a piece of hardware (or the mapping,
compilation or exploration of hardware) whose stated purpose is executing machine-learning workloads?**
Answer `yes`, `no` or `borderline`. Memory-centric computing hardware is `yes` only if the abstract
connects it to neural networks, AI, or the matrix/vector kernels of such workloads. If `no`, also answer
`gate_reason_if_no`: is it machine learning applied to chip design or test (`ai_for_eda`); a model or
learning method without hardware (`ai_algorithm_only`); attacking, protecting or testing AI where
hardware is not what is new (`security_or_test_of_ai`); hardware with no machine-learning workload
(`not_ai`); or `other`? For a `no` paper give only `id`, `is_ai_hardware`, `gate_reason_if_no`.

For `yes` and `borderline` papers:

**Q1 `A7_scale` — How big is the object being designed?** A cell/array/converter/memory block
(`macro_circuit`); a single engine or core (`engine_core`); a group of engines or cores around one local
memory, or a tile (`cluster_tile`); a complete chip (`soc_chip`); several dies or chiplets
(`multi_chip_chiplet`); racks or a datacentre (`system_datacenter`); no hardware object, a flow or tool
(`tool_only`); `not_stated`.

**Q2 `A1_paradigm` — By what physical means is the arithmetic done?** Ordinary digital logic in a
purpose-built datapath (`digital_spatial_asic`); a systolic array or dedicated matrix multiplier, if the
text uses those words (`systolic_matrix_engine`); vector/SIMD hardware or new instructions on a
programmable processor (`vector_simd_isa_ext`); a reconfigurable dataflow fabric (`cgra_dataflow`); a GPU
(`gpu_simt`); an FPGA as the intended platform (`fpga`); inside an SRAM array with analog accumulation
(`cim_analog_sram`); inside a non-volatile array such as RRAM, PCM, FeFET, MRAM, flash or a memristor
crossbar (`cim_analog_nvm`); inside a memory array but with purely digital arithmetic (`cim_digital`);
inside or beside DRAM/HBM (`pim_dram_near_memory`); light (`photonic`); spikes/events (`neuromorphic`);
stochastic or approximate arithmetic (`stochastic_or_approximate`); no means of its own because the paper
is a tool or method (`target_generic`); `not_stated`; `other`. An in-memory paper silent on analog versus
digital: non-volatile memory → `cim_analog_nvm`; SRAM → `cim_analog_sram` only when ADCs, charge, current
or bit-line sensing are mentioned, otherwise `not_stated`.

**Q3 `A1_device` — Which memory technology is the computation tied to?** `sram`, `rram`, `pcm`, `fefet`,
`mram`, `dram`, `flash`, `gain_cell`, `other`; `none` if no memory technology is part of the idea;
`not_stated` if it is an in-memory design that never names one.

**Q4 `A0_workload` — Which model family carries the main result?** `cnn`; `transformer_encoder_vit`
(encoder or vision transformers, attention blocks, no token-by-token generation);
`llm_autoregressive` (language models generating tokens, decoding, KV cache); `gnn`; `snn`; `rnn_lstm`;
`recommendation`; `generative_diffusion`; `training` (learning itself is what is accelerated); `non_nn`;
`generic_dnn` (only "DNN", "AI", "neural network" or MLP); `not_stated`; `other`.

**Q5 `lever` — What does the paper change to get its result?** Give 1–3, strongest first:
`circuit_macro_design`; `dataflow_tiling_buffering`; `memory_hierarchy`; `interconnect_noc_chiplet`;
`mapping_dse_compiler`; `scheduling_control`; `precision_format`; `sparsity`;
`nonideality_reliability` (variation, noise, drift, faults, IR drop, endurance);
`programmability_sw_stack`; `on_device_training`; `power_thermal`; `security`; `other`.

**Q6 `A2_data_residency` — Where do the operands sit, and by what route do they arrive?**
`in_array_weights` (weights remain in the computing array); `scratchpad_dma` (a software-managed local
memory filled by explicit transfers); `shared_l1_cluster` (one local memory shared by several units);
`noc_mesh_tiles` (units linked by an on-chip network); `cache_hierarchy`; `stacked_3d`;
`chiplet_multi_die`; `hbm_or_dram_bound` (organised around main-memory bandwidth); `not_stated`; `other`.

**Q7 `A3_numerics` — In what number format are values computed?** `fp32`, `fp16_bf16`, `fp8`, `int8`,
`int4_or_less`, `binary_ternary`, `mixed_or_variable`, `block_microscaling`, `bit_serial`,
`posit_or_lns`, `analog_levels` (multi-level conductances, no digital format given), `not_stated`, `other`.

**Q8 `A4_sparsity_codesign` — Does the result depend on changing the model or its training?**
`none_stated`; `unstructured_sparsity`; `structured_sparsity`; `pruning_hw_codesign`;
`quantization_aware` (training or calibration fitted to the hardware's precision or imperfections);
`token_or_attention_sparsity`; `nas_hw_codesign`; `other`.

**Q9 `A5_programmability` — How does software drive it?** New instructions (`isa_extension`); a
coprocessor bound to a core (`tightly_coupled_coprocessor`); a register-controlled engine working on a
memory it shares with the cores (`memory_mapped_shared_l1_engine`); a self-contained accelerator
(`standalone_accelerator`); a host that ships jobs to a device (`host_offload`); nothing programmable
(`fixed_function`); `not_stated`; `other`.

**Q10 `A6_eval_rung` — What is the strongest kind of evidence behind the headline number?** A measured
fabricated chip (`silicon`); a measured deployed system (`board_or_system`); layout-level results
(`post_layout`); synthesis results (`post_synthesis`); an FPGA implementation (`fpga`); RTL simulation
(`rtl_sim`); circuit, architecture or framework simulation (`simulator`); equations or models
(`analytical`); `not_stated`.

**Q11 `A6_baseline_class` — Against what is the headline number compared?** `cpu`; `gpu`;
`prior_accelerator` (earlier designs, named or "state of the art"); `own_variant_only`; `none_stated`.

**Q12 `design_method` — Does the abstract say how the hardware description was produced?** `hand_rtl`,
`hls`, `generator`, `ai_generated`, `not_stated`.

Write one JSON object per paper on its own line with these keys and `id`. Nothing else in the file.
