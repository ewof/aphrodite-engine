#pragma once

#include <torch/library.h>

#ifndef USE_ROCM
// AQLM
torch::Tensor aqlm_gemm(const torch::Tensor& input, const torch::Tensor& codes,
                        const torch::Tensor& codebooks,
                        const torch::Tensor& scales,
                        const torch::Tensor& codebook_partition_sizes,
                        const std::optional<torch::Tensor>& bias);

torch::Tensor aqlm_dequant(const torch::Tensor& codes,
                           const torch::Tensor& codebooks,
                           const torch::Tensor& codebook_partition_sizes);

// AWQ
torch::Tensor awq_gemm(torch::Tensor _in_feats, torch::Tensor _kernel,
                       torch::Tensor _scaling_factors, torch::Tensor _zeros,
                       int64_t split_k_iters);

torch::Tensor awq_dequantize(torch::Tensor _kernel,
                             torch::Tensor _scaling_factors,
                             torch::Tensor _zeros, int64_t split_k_iters,
                             int64_t thx, int64_t thy);

torch::Tensor awq_group_gemm(torch::Tensor _in_feats, torch::Tensor _kernel,
                             torch::Tensor _scaling_factors,
                             torch::Tensor _zeros, torch::Tensor _topk_weights,
                             torch::Tensor _sorted_token_ids_ptr,
                             torch::Tensor _expert_ids_ptr,
                             torch::Tensor _num_tokens_post_padded,
                             bool mul_weights, int64_t split_k_iters);
#endif

// GPTQ
torch::Tensor gptq_gemm(torch::Tensor a, torch::Tensor b_q_weight,
                        torch::Tensor b_gptq_qzeros,
                        torch::Tensor b_gptq_scales, torch::Tensor b_g_idx,
                        bool use_exllama, int64_t bit);

void gptq_shuffle(torch::Tensor q_weight, torch::Tensor q_perm, int64_t bit);

torch::Tensor group_gptq_gemm(torch::Tensor a, torch::Tensor b_q_weight,
                              torch::Tensor b_gptq_qzeros,
                              torch::Tensor b_gptq_scales,
                              torch::Tensor b_g_idx, torch::Tensor topk_weights,
                              torch::Tensor sorted_token_ids_ptr,
                              torch::Tensor expert_ids_ptr,
                              torch::Tensor num_tokens_post_padded,
                              bool mul_weights, bool use_exllama);

torch::Tensor dequant_gptq(torch::Tensor b_q_weight,
                           torch::Tensor b_gptq_qzeros,
                           torch::Tensor b_gptq_scales, torch::Tensor b_g_idx,
                           int64_t bits, bool use_exllama);

#ifndef USE_ROCM
// Marlin
torch::Tensor marlin_gemm(torch::Tensor& a, torch::Tensor& b_q_weight,
                          torch::Tensor& b_scales, torch::Tensor& workspace,
                          int64_t size_m, int64_t size_n, int64_t size_k);

torch::Tensor gptq_marlin_24_gemm(torch::Tensor& a, torch::Tensor& b_q_weight,
                                  torch::Tensor& b_meta,
                                  torch::Tensor& b_scales,
                                  torch::Tensor& workspace, int64_t num_bits,
                                  int64_t size_m, int64_t size_n,
                                  int64_t size_k);

torch::Tensor gptq_marlin_gemm(torch::Tensor& a, torch::Tensor& b_q_weight,
                               torch::Tensor& b_scales, torch::Tensor& g_idx,
                               torch::Tensor& perm, torch::Tensor& workspace,
                               int64_t num_bits, int64_t size_m, int64_t size_n,
                               int64_t size_k, bool is_k_full);

torch::Tensor gptq_marlin_repack(torch::Tensor& b_q_weight, torch::Tensor& perm,
                                 int64_t size_k, int64_t size_n,
                                 int64_t num_bits);

// QuIP#
at::Tensor e8p_mm_origorder(const at::Tensor& A, const at::Tensor& B,
                            const at::Tensor& CB);

void decompress_e8p_origorder(torch::Tensor YIs, torch::Tensor CB,
                              torch::Tensor& Y);

void cutlass_scaled_mm_dq(torch::Tensor& out, torch::Tensor const& a,
                          torch::Tensor const& b, torch::Tensor const& a_scales,
                          torch::Tensor const& b_scales);

#endif

void static_scaled_int8_quant(torch::Tensor& out, torch::Tensor const& input,
                              torch::Tensor const& scale);

void dynamic_scaled_int8_quant(torch::Tensor& out, torch::Tensor const& input,
                               torch::Tensor& scales);

// SqueezeLLM
void squeezellm_gemm(torch::Tensor vec, torch::Tensor mat, torch::Tensor mul,
                     torch::Tensor lookup_table);

// FP8
void static_scaled_fp8_quant(torch::Tensor& out, torch::Tensor& input,
                             torch::Tensor& scale);

void dynamic_scaled_fp8_quant(torch::Tensor& out, torch::Tensor& input,
                              torch::Tensor& scale);
