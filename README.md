# LLMSCAN

## Reproduced Bug Report

### Reproduced Report List



### TODO List

#### Case I:

- https://github.com/openssl/openssl/pull/19266/commits/674c2c5aa77c903f51ad3d7f8d750874b6f2388c

- commit id: ec59752

- Buggy file: /Users/xiangqian/Documents/CodeBase/LLMDFuzz/benchmark/C/openssl/crypto/sm2/sm2_sign.c

- Bug description: To match the BN_CTX_start, it should be better to add BN_CTX_end in the end of the function.

- Similar bugs:

  - https://github.com/openssl/openssl/blob/d8def79838cd0d5e7c21d217aa26edb5229f0ab4/crypto/sm2/sm2_crypt.c#L107


## Problem Formulation

Input setting:

- Option 1: Given API specifications (in natural languages)

- Option 2: Given the resource initilization API only

Outputs:

- Bug reports of resource leakage (intra-procedural although it may have low recall)

Target system:

- Linux Kernal?

## Pattern Summary

Pattern 1: If the function API applies a resource and the resource does not esacape out of the current function, the resource should be freed after the initialization in the current function.

Pattern 2: (Linux b3236a64). Multiple objects pointed by different fields of memory objects. Although the objects may escape, other fields correponding to the errors have been cleared.

## Specification Examples

- a = kmalloc()

  - Ret value: can be null. check nullity before use

  - Ret value: release the resouce (memory) after use

  - Free API: free(a) free the object the base pointer of a

  - Similar APIs: mhi_alloc_controller/mhi_free_controller

  - Examples: fea3fdf975dd


## Workflow

- Extract the Use Trace (API use & Operator use & escape use) starting from function entry to each return point

- LLM-based analysis: Alias analysis + Escape analysis (For intra-procedural bug detection)



