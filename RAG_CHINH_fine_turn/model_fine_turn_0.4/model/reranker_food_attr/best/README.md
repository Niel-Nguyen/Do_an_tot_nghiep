---
tags:
- sentence-transformers
- cross-encoder
- reranker
- generated_from_trainer
- dataset_size:20160
- loss:BinaryCrossEntropyLoss
base_model: cross-encoder/ms-marco-MiniLM-L6-v2
pipeline_tag: text-ranking
library_name: sentence-transformers
---

# CrossEncoder based on cross-encoder/ms-marco-MiniLM-L6-v2

This is a [Cross Encoder](https://www.sbert.net/docs/cross_encoder/usage/usage.html) model finetuned from [cross-encoder/ms-marco-MiniLM-L6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2) using the [sentence-transformers](https://www.SBERT.net) library. It computes scores for pairs of texts, which can be used for text reranking and semantic search.

## Model Details

### Model Description
- **Model Type:** Cross Encoder
- **Base model:** [cross-encoder/ms-marco-MiniLM-L6-v2](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2) <!-- at revision ce0834f22110de6d9222af7a7a03628121708969 -->
- **Maximum Sequence Length:** 224 tokens
- **Number of Output Labels:** 1 label
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Documentation:** [Cross Encoder Documentation](https://www.sbert.net/docs/cross_encoder/usage/usage.html)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/UKPLab/sentence-transformers)
- **Hugging Face:** [Cross Encoders on Hugging Face](https://huggingface.co/models?library=sentence-transformers&other=cross-encoder)

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import CrossEncoder

# Download from the 🤗 Hub
model = CrossEncoder("cross_encoder_model_id")
# Get scores for pairs of texts
pairs = [
    ['Tư vấn giúp món giá trung bình', '[Region: Nam][Mood: Vui vẻ][Type: Vặt][Veg: Mặn][Texture: Khô][PriceBucket: trung][TimeBucket: trung]\nMón ăn: Gỏi Cuốn Tôm Chua\nMô tả: Những món cuốn luôn là món ăn nổi bật trên bàn ăn, nhờ có vị ngon hấp dẫn và hình thức cực…. Giàu đạm khá béo.'],
    ['Cho mình món hợp tâm trạng Vui vẻ', '[Region: Bắc][Mood: Thư giãn][Type: Chính][Veg: Mặn][Texture: Nước][PriceBucket: trung][TimeBucket: nhanh]\nMón ăn: Phở Gạo Lứt Xào Xúc Xích Rau Củ\nMô tả: Phở gạo lứt xào xúc xích rau củ là món ngon dễ làm cho bữa ăn gia đình bạn thêm phong phú…. Nhẹ đạm khá béo.'],
    ['Cho mình món giá dễ chịu', '[Region: Bắc][Mood: Thư giãn][Type: Chính][Veg: Mặn][Texture: Nước][PriceBucket: rẻ][TimeBucket: bận]\nMón ăn: Bún Quậy Phú Quốc\nMô tả: Nhiều người rỉ rả nhau rằng đến Phú Quốc mà không ăn bún quậy là phí cả một chuyến đi nhưng nào…. Giàu đạm khá béo.'],
    ['Gợi ý món giá dễ chịu', '[Region: Bắc][Mood: Hào hứng][Type: Vặt][Veg: Mặn][Texture: Khô][PriceBucket: trung][TimeBucket: trung]\nMón ăn: Chả cá chiên bánh tráng\nMô tả: Chỉ tốn 10 phút là gia đình bạn có ngay món Chả cá chiên bánh tránh lạ miệng vô cùng. Chả cá…. Đạm ở mức vừa độ béo trung bình.'],
    ['Cho tôi món miền Bắc', '[Region: Bắc][Mood: Ấm áp][Type: Chính][Veg: Mặn][Texture: Nước][PriceBucket: trung][TimeBucket: trung]\nMón ăn: Bún gạo xào thập cẩm\nMô tả: Bún gạo xào thập cẩm là một món ăn ngon miệng mà vô cùng đơn giản, rất tốt cho sức khỏe với…. Đạm ở mức vừa khá béo.'],
]
scores = model.predict(pairs)
print(scores.shape)
# (5,)

# Or rank different texts based on similarity to a single text
ranks = model.rank(
    'Tư vấn giúp món giá trung bình',
    [
        '[Region: Nam][Mood: Vui vẻ][Type: Vặt][Veg: Mặn][Texture: Khô][PriceBucket: trung][TimeBucket: trung]\nMón ăn: Gỏi Cuốn Tôm Chua\nMô tả: Những món cuốn luôn là món ăn nổi bật trên bàn ăn, nhờ có vị ngon hấp dẫn và hình thức cực…. Giàu đạm khá béo.',
        '[Region: Bắc][Mood: Thư giãn][Type: Chính][Veg: Mặn][Texture: Nước][PriceBucket: trung][TimeBucket: nhanh]\nMón ăn: Phở Gạo Lứt Xào Xúc Xích Rau Củ\nMô tả: Phở gạo lứt xào xúc xích rau củ là món ngon dễ làm cho bữa ăn gia đình bạn thêm phong phú…. Nhẹ đạm khá béo.',
        '[Region: Bắc][Mood: Thư giãn][Type: Chính][Veg: Mặn][Texture: Nước][PriceBucket: rẻ][TimeBucket: bận]\nMón ăn: Bún Quậy Phú Quốc\nMô tả: Nhiều người rỉ rả nhau rằng đến Phú Quốc mà không ăn bún quậy là phí cả một chuyến đi nhưng nào…. Giàu đạm khá béo.',
        '[Region: Bắc][Mood: Hào hứng][Type: Vặt][Veg: Mặn][Texture: Khô][PriceBucket: trung][TimeBucket: trung]\nMón ăn: Chả cá chiên bánh tráng\nMô tả: Chỉ tốn 10 phút là gia đình bạn có ngay món Chả cá chiên bánh tránh lạ miệng vô cùng. Chả cá…. Đạm ở mức vừa độ béo trung bình.',
        '[Region: Bắc][Mood: Ấm áp][Type: Chính][Veg: Mặn][Texture: Nước][PriceBucket: trung][TimeBucket: trung]\nMón ăn: Bún gạo xào thập cẩm\nMô tả: Bún gạo xào thập cẩm là một món ăn ngon miệng mà vô cùng đơn giản, rất tốt cho sức khỏe với…. Đạm ở mức vừa khá béo.',
    ]
)
# [{'corpus_id': ..., 'score': ...}, {'corpus_id': ..., 'score': ...}, ...]
```

<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 20,160 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 1000 samples:
  |         | sentence_0                                                                                     | sentence_1                                                                                        | label                                                          |
  |:--------|:-----------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------|:---------------------------------------------------------------|
  | type    | string                                                                                         | string                                                                                            | float                                                          |
  | details | <ul><li>min: 13 characters</li><li>mean: 24.86 characters</li><li>max: 47 characters</li></ul> | <ul><li>min: 205 characters</li><li>mean: 258.09 characters</li><li>max: 288 characters</li></ul> | <ul><li>min: 0.0</li><li>mean: 0.27</li><li>max: 1.0</li></ul> |
* Samples:
  | sentence_0                                     | sentence_1                                                                                                                                                                                                                                                                                | label            |
  |:-----------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|
  | <code>Tư vấn giúp món giá trung bình</code>    | <code>[Region: Nam][Mood: Vui vẻ][Type: Vặt][Veg: Mặn][Texture: Khô][PriceBucket: trung][TimeBucket: trung]<br>Món ăn: Gỏi Cuốn Tôm Chua<br>Mô tả: Những món cuốn luôn là món ăn nổi bật trên bàn ăn, nhờ có vị ngon hấp dẫn và hình thức cực…. Giàu đạm khá béo.</code>                  | <code>1.0</code> |
  | <code>Cho mình món hợp tâm trạng Vui vẻ</code> | <code>[Region: Bắc][Mood: Thư giãn][Type: Chính][Veg: Mặn][Texture: Nước][PriceBucket: trung][TimeBucket: nhanh]<br>Món ăn: Phở Gạo Lứt Xào Xúc Xích Rau Củ<br>Mô tả: Phở gạo lứt xào xúc xích rau củ là món ngon dễ làm cho bữa ăn gia đình bạn thêm phong phú…. Nhẹ đạm khá béo.</code> | <code>0.0</code> |
  | <code>Cho mình món giá dễ chịu</code>          | <code>[Region: Bắc][Mood: Thư giãn][Type: Chính][Veg: Mặn][Texture: Nước][PriceBucket: rẻ][TimeBucket: bận]<br>Món ăn: Bún Quậy Phú Quốc<br>Mô tả: Nhiều người rỉ rả nhau rằng đến Phú Quốc mà không ăn bún quậy là phí cả một chuyến đi nhưng nào…. Giàu đạm khá béo.</code>             | <code>0.0</code> |
* Loss: [<code>BinaryCrossEntropyLoss</code>](https://sbert.net/docs/package_reference/cross_encoder/losses.html#binarycrossentropyloss) with these parameters:
  ```json
  {
      "activation_fn": "torch.nn.modules.linear.Identity",
      "pos_weight": null
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `per_device_train_batch_size`: 16
- `per_device_eval_batch_size`: 16
- `num_train_epochs`: 1

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `overwrite_output_dir`: False
- `do_predict`: False
- `eval_strategy`: no
- `prediction_loss_only`: True
- `per_device_train_batch_size`: 16
- `per_device_eval_batch_size`: 16
- `per_gpu_train_batch_size`: None
- `per_gpu_eval_batch_size`: None
- `gradient_accumulation_steps`: 1
- `eval_accumulation_steps`: None
- `torch_empty_cache_steps`: None
- `learning_rate`: 5e-05
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `max_grad_norm`: 1
- `num_train_epochs`: 1
- `max_steps`: -1
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: {}
- `warmup_ratio`: 0.0
- `warmup_steps`: 0
- `log_level`: passive
- `log_level_replica`: warning
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `save_safetensors`: True
- `save_on_each_node`: False
- `save_only_model`: False
- `restore_callback_states_from_checkpoint`: False
- `no_cuda`: False
- `use_cpu`: False
- `use_mps_device`: False
- `seed`: 42
- `data_seed`: None
- `jit_mode_eval`: False
- `use_ipex`: False
- `bf16`: False
- `fp16`: False
- `fp16_opt_level`: O1
- `half_precision_backend`: auto
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `local_rank`: 0
- `ddp_backend`: None
- `tpu_num_cores`: None
- `tpu_metrics_debug`: False
- `debug`: []
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_prefetch_factor`: None
- `past_index`: -1
- `disable_tqdm`: False
- `remove_unused_columns`: True
- `label_names`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `fsdp`: []
- `fsdp_min_num_params`: 0
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `fsdp_transformer_layer_cls_to_wrap`: None
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `deepspeed`: None
- `label_smoothing_factor`: 0.0
- `optim`: adamw_torch_fused
- `optim_args`: None
- `adafactor`: False
- `group_by_length`: False
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `skip_memory_metrics`: True
- `use_legacy_prediction_loop`: False
- `push_to_hub`: False
- `resume_from_checkpoint`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_private_repo`: None
- `hub_always_push`: False
- `hub_revision`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `include_inputs_for_metrics`: False
- `include_for_metrics`: []
- `eval_do_concat_batches`: True
- `fp16_backend`: auto
- `push_to_hub_model_id`: None
- `push_to_hub_organization`: None
- `mp_parameters`: 
- `auto_find_batch_size`: False
- `full_determinism`: False
- `torchdynamo`: None
- `ray_scope`: last
- `ddp_timeout`: 1800
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `include_tokens_per_second`: False
- `include_num_input_tokens_seen`: False
- `neftune_noise_alpha`: None
- `optim_target_modules`: None
- `batch_eval_metrics`: False
- `eval_on_start`: False
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `eval_use_gather_object`: False
- `average_tokens_across_devices`: False
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: proportional
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Training Logs
| Epoch  | Step | Training Loss |
|:------:|:----:|:-------------:|
| 0.3968 | 500  | 0.6581        |
| 0.7937 | 1000 | 0.5382        |
| 0.3968 | 500  | 0.5331        |
| 0.7937 | 1000 | 0.524         |
| 0.3968 | 500  | 0.5222        |
| 0.7937 | 1000 | 0.51          |
| 0.3968 | 500  | 0.507         |
| 0.7937 | 1000 | 0.4856        |
| 0.3968 | 500  | 0.4926        |
| 0.7937 | 1000 | 0.4832        |
| 0.3968 | 500  | 0.4844        |
| 0.7937 | 1000 | 0.47          |


### Framework Versions
- Python: 3.9.23
- Sentence Transformers: 5.1.0
- Transformers: 4.55.2
- PyTorch: 2.8.0+cpu
- Accelerate: 1.10.0
- Datasets: 4.0.0
- Tokenizers: 0.21.4

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->