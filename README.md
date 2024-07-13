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