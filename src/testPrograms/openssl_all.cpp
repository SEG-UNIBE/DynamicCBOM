// Compile (Linux):
//   g++ -std=c++17 -Wall openssl_all.cpp -lcrypto -o openssl_demo
//
// This example demonstrates:
//   * AES-256-GCM symmetric encryption/decryption (AEAD)
//   * RSA-2048 key generation
//   * RSA-OAEP encryption/decryption (with SHA-256)
//   * RSA-PSS signing/verification (with SHA-256)
//   * SHA-256 hashing via EVP_Digest*
//   * HMAC-SHA-256 via HMAC()

#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/err.h>
#include <openssl/hmac.h>
#include <openssl/pem.h>
#include <openssl/rsa.h>

#include <iostream>
#include <vector>
#include <string>
#include <cstdlib>
#include <cstdio>

static void handleErrors() {
    ERR_print_errors_fp(stderr);
    std::abort();
}

static void printHex(const std::string &label,
                     const unsigned char *data,
                     std::size_t len) {
    std::cout << label << " (" << len << "): ";
    for (std::size_t i = 0; i < len; ++i) {
        std::printf("%02x", data[i]);
    }
    std::cout << std::endl;
}

// ============================================================================
// 1. Symmetric AES-256-GCM (AEAD)
// ============================================================================

int aes_gcm_encrypt(const unsigned char *plaintext, int plaintext_len,
                    const unsigned char *aad, int aad_len,
                    const unsigned char *key,
                    const unsigned char *iv, int iv_len,
                    unsigned char *ciphertext,
                    unsigned char *tag) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    int len = 0;
    int ciphertext_len = 0;

    if (!ctx)
        handleErrors();

    // Use AES-256-GCM
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr) != 1)
        handleErrors();

    // Set IV length
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, iv_len, nullptr) != 1)
        handleErrors();

    // Set key and IV
    if (EVP_EncryptInit_ex(ctx, nullptr, nullptr, key, iv) != 1)
        handleErrors();

    // AAD (optional)
    if (aad && aad_len > 0) {
        if (EVP_EncryptUpdate(ctx, nullptr, &len, aad, aad_len) != 1)
            handleErrors();
    }

    // Encrypt plaintext
    if (EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, plaintext_len) != 1)
        handleErrors();
    ciphertext_len = len;

    // Finalize (GCM does not output extra ciphertext here, but keep pattern)
    if (EVP_EncryptFinal_ex(ctx, ciphertext + len, &len) != 1)
        handleErrors();
    ciphertext_len += len;

    // Get authentication tag
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, tag) != 1)
        handleErrors();

    EVP_CIPHER_CTX_free(ctx);
    return ciphertext_len;
}

int aes_gcm_decrypt(const unsigned char *ciphertext, int ciphertext_len,
                    const unsigned char *aad, int aad_len,
                    const unsigned char *tag,
                    const unsigned char *key,
                    const unsigned char *iv, int iv_len,
                    unsigned char *plaintext) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    int len = 0;
    int plaintext_len = 0;
    int ret;

    if (!ctx)
        handleErrors();

    // Use AES-256-GCM
    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr) != 1)
        handleErrors();

    // Set IV length
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, iv_len, nullptr) != 1)
        handleErrors();

    // Set key and IV
    if (EVP_DecryptInit_ex(ctx, nullptr, nullptr, key, iv) != 1)
        handleErrors();

    // AAD (optional)
    if (aad && aad_len > 0) {
        if (EVP_DecryptUpdate(ctx, nullptr, &len, aad, aad_len) != 1)
            handleErrors();
    }

    // Decrypt ciphertext
    if (EVP_DecryptUpdate(ctx, plaintext, &len, ciphertext, ciphertext_len) != 1)
        handleErrors();
    plaintext_len = len;

    // Set expected tag before finalization
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, 16,
                            const_cast<unsigned char *>(tag)) != 1)
        handleErrors();

    // Verify tag
    ret = EVP_DecryptFinal_ex(ctx, plaintext + len, &len);

    EVP_CIPHER_CTX_free(ctx);

    if (ret > 0) {
        plaintext_len += len;
        return plaintext_len; // success
    } else {
        return -1; // authentication failed
    }
}

// ============================================================================
// 2. Hashing: SHA-256 and HMAC-SHA-256
// ============================================================================

std::vector<unsigned char> sha256_digest(const std::vector<unsigned char> &data) {
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    if (!ctx)
        handleErrors();

    if (EVP_DigestInit_ex(ctx, EVP_sha256(), nullptr) != 1)
        handleErrors();

    if (EVP_DigestUpdate(ctx, data.data(), data.size()) != 1)
        handleErrors();

    unsigned char md[EVP_MAX_MD_SIZE];
    unsigned int md_len = 0;

    if (EVP_DigestFinal_ex(ctx, md, &md_len) != 1)
        handleErrors();

    EVP_MD_CTX_free(ctx);

    return std::vector<unsigned char>(md, md + md_len);
}

std::vector<unsigned char> hmac_sha256(const std::vector<unsigned char> &key,
                                       const std::vector<unsigned char> &data) {
    unsigned int len = EVP_MAX_MD_SIZE;
    std::vector<unsigned char> out(len);

    if (!HMAC(EVP_sha256(),
              key.data(), static_cast<int>(key.size()),
              data.data(), data.size(),
              out.data(), &len)) {
        handleErrors();
    }

    out.resize(len);
    return out;
}

// ============================================================================
// 3. Asymmetric: RSA-2048 keygen, OAEP, PSS
// ============================================================================

// Generate RSA-2048 key pair using EVP_PKEY APIs
EVP_PKEY *generate_rsa_2048_key() {
    EVP_PKEY *pkey = nullptr;
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_RSA, nullptr);
    if (!ctx)
        handleErrors();

    if (EVP_PKEY_keygen_init(ctx) <= 0)
        handleErrors();

    if (EVP_PKEY_CTX_set_rsa_keygen_bits(ctx, 2048) <= 0)
        handleErrors();

    if (EVP_PKEY_keygen(ctx, &pkey) <= 0)
        handleErrors();

    EVP_PKEY_CTX_free(ctx);
    return pkey;
}

// RSA-OAEP encryption with SHA-256
std::vector<unsigned char> rsa_oaep_encrypt(EVP_PKEY *pubkey,
                                            const std::vector<unsigned char> &plaintext) {
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(pubkey, nullptr);
    if (!ctx)
        handleErrors();

    if (EVP_PKEY_encrypt_init(ctx) <= 0)
        handleErrors();

    if (EVP_PKEY_CTX_set_rsa_padding(ctx, RSA_PKCS1_OAEP_PADDING) <= 0)
        handleErrors();

    if (EVP_PKEY_CTX_set_rsa_oaep_md(ctx, EVP_sha256()) <= 0)
        handleErrors();

    // First call: get required buffer length
    size_t outlen = 0;
    if (EVP_PKEY_encrypt(ctx, nullptr, &outlen,
                         plaintext.data(), plaintext.size()) <= 0) {
        handleErrors();
    }

    std::vector<unsigned char> ciphertext(outlen);

    // Second call: actual encryption
    if (EVP_PKEY_encrypt(ctx, ciphertext.data(), &outlen,
                         plaintext.data(), plaintext.size()) <= 0) {
        handleErrors();
    }

    ciphertext.resize(outlen);
    EVP_PKEY_CTX_free(ctx);
    return ciphertext;
}

// RSA-OAEP decryption with SHA-256
std::vector<unsigned char> rsa_oaep_decrypt(EVP_PKEY *privkey,
                                            const std::vector<unsigned char> &ciphertext) {
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(privkey, nullptr);
    if (!ctx)
        handleErrors();

    if (EVP_PKEY_decrypt_init(ctx) <= 0)
        handleErrors();

    if (EVP_PKEY_CTX_set_rsa_padding(ctx, RSA_PKCS1_OAEP_PADDING) <= 0)
        handleErrors();

    if (EVP_PKEY_CTX_set_rsa_oaep_md(ctx, EVP_sha256()) <= 0)
        handleErrors();

    size_t outlen = 0;
    if (EVP_PKEY_decrypt(ctx, nullptr, &outlen,
                         ciphertext.data(), ciphertext.size()) <= 0) {
        handleErrors();
    }

    std::vector<unsigned char> plaintext(outlen);

    if (EVP_PKEY_decrypt(ctx, plaintext.data(), &outlen,
                         ciphertext.data(), ciphertext.size()) <= 0) {
        handleErrors();
    }

    plaintext.resize(outlen);
    EVP_PKEY_CTX_free(ctx);
    return plaintext;
}

// RSA-PSS sign with SHA-256 via EVP_DigestSign*
std::vector<unsigned char> rsa_pss_sign(EVP_PKEY *privkey,
                                        const std::vector<unsigned char> &message) {
    EVP_MD_CTX *mdctx = EVP_MD_CTX_new();
    if (!mdctx)
        handleErrors();

    if (EVP_DigestSignInit(mdctx, nullptr, EVP_sha256(), nullptr, privkey) <= 0)
        handleErrors();

    // PSS padding is default in many configs, but we can be explicit if needed
    // via EVP_PKEY_CTX_set_rsa_padding(...). For simplicity, use defaults here.

    if (EVP_DigestSignUpdate(mdctx, message.data(), message.size()) <= 0)
        handleErrors();

    size_t siglen = 0;
    if (EVP_DigestSignFinal(mdctx, nullptr, &siglen) <= 0)
        handleErrors();

    std::vector<unsigned char> signature(siglen);

    if (EVP_DigestSignFinal(mdctx, signature.data(), &siglen) <= 0)
        handleErrors();

    signature.resize(siglen);
    EVP_MD_CTX_free(mdctx);
    return signature;
}

// RSA-PSS verify with SHA-256 via EVP_DigestVerify*
bool rsa_pss_verify(EVP_PKEY *pubkey,
                    const std::vector<unsigned char> &message,
                    const std::vector<unsigned char> &signature) {
    EVP_MD_CTX *mdctx = EVP_MD_CTX_new();
    if (!mdctx)
        handleErrors();

    if (EVP_DigestVerifyInit(mdctx, nullptr, EVP_sha256(), nullptr, pubkey) <= 0)
        handleErrors();

    if (EVP_DigestVerifyUpdate(mdctx, message.data(), message.size()) <= 0)
        handleErrors();

    int ok = EVP_DigestVerifyFinal(mdctx,
                                   signature.data(), signature.size());

    EVP_MD_CTX_free(mdctx);
    return ok == 1; // 1 = success, 0 = bad signature, <0 = error
}

// ============================================================================
// main(): glue everything together
// ============================================================================

int main() {
    // Print OpenSSL errors in readable form
    ERR_load_crypto_strings();

    // ------------------------------------------------------------------------
    // Symmetric AES-256-GCM demo
    // ------------------------------------------------------------------------
    const std::string msg = "Dynamic CBOM loves OpenSSL!";
    std::vector<unsigned char> msg_bytes(msg.begin(), msg.end());

    unsigned char aes_key[32];   // 256-bit key
    unsigned char aes_iv[12];    // 96-bit IV (recommended for GCM)
    if (RAND_bytes(aes_key, sizeof(aes_key)) != 1 ||
        RAND_bytes(aes_iv, sizeof(aes_iv)) != 1) {
        handleErrors();
    }

    std::vector<unsigned char> ciphertext(msg_bytes.size() + 16);
    unsigned char tag[16];

    int ciphertext_len = aes_gcm_encrypt(
        msg_bytes.data(), static_cast<int>(msg_bytes.size()),
        nullptr, 0,                // no AAD
        aes_key,
        aes_iv, sizeof(aes_iv),
        ciphertext.data(),
        tag
    );
    ciphertext.resize(ciphertext_len);

    printHex("AES-256-GCM ciphertext", ciphertext.data(), ciphertext.size());
    printHex("AES-256-GCM tag", tag, sizeof(tag));

    std::vector<unsigned char> decrypted(msg_bytes.size() + 16);
    int decrypted_len = aes_gcm_decrypt(
        ciphertext.data(), ciphertext_len,
        nullptr, 0,
        tag,
        aes_key,
        aes_iv, sizeof(aes_iv),
        decrypted.data()
    );

    if (decrypted_len < 0) {
        std::cerr << "AES-GCM decryption failed (tag mismatch)\n";
        return 1;
    }
    decrypted.resize(decrypted_len);

    std::cout << "AES-256-GCM decrypted: "
              << std::string(decrypted.begin(), decrypted.end()) << "\n\n";

    // ------------------------------------------------------------------------
    // Hashing: SHA-256 and HMAC-SHA-256
    // ------------------------------------------------------------------------
    auto sha = sha256_digest(msg_bytes);
    printHex("SHA-256(msg)", sha.data(), sha.size());

    std::vector<unsigned char> hmac_key(16);
    if (RAND_bytes(hmac_key.data(), static_cast<int>(hmac_key.size())) != 1)
        handleErrors();

    auto mac = hmac_sha256(hmac_key, msg_bytes);
    printHex("HMAC-SHA-256(msg)", mac.data(), mac.size());
    std::cout << std::endl;

    // ------------------------------------------------------------------------
    // Asymmetric RSA-2048: OAEP encryption/decryption + PSS sign/verify
    // ------------------------------------------------------------------------
    EVP_PKEY *rsa_key = generate_rsa_2048_key();
    if (!rsa_key) {
        std::cerr << "Failed to generate RSA key\n";
        return 1;
    }

    // Encrypt with RSA-OAEP + SHA-256
    auto rsa_cipher = rsa_oaep_encrypt(rsa_key, msg_bytes);
    printHex("RSA-OAEP ciphertext", rsa_cipher.data(), rsa_cipher.size());

    // Decrypt with RSA-OAEP + SHA-256
    auto rsa_plain = rsa_oaep_decrypt(rsa_key, rsa_cipher);
    std::cout << "RSA-OAEP decrypted: "
              << std::string(rsa_plain.begin(), rsa_plain.end()) << "\n\n";

    // Sign with RSA-PSS + SHA-256
    auto signature = rsa_pss_sign(rsa_key, msg_bytes);
    printHex("RSA-PSS signature", signature.data(), signature.size());

    // Verify with RSA-PSS + SHA-256
    bool ok = rsa_pss_verify(rsa_key, msg_bytes, signature);
    std::cout << "RSA-PSS verification: " << (ok ? "SUCCESS" : "FAILURE") << "\n";

    // Optionally, dump the private key in PEM for inspection (commented out):
    /*
    PEM_write_PrivateKey(stdout, rsa_key, nullptr, nullptr, 0, nullptr, nullptr);
    */

    EVP_PKEY_free(rsa_key);
    ERR_free_strings(); // optional in short-lived programs

    return ok ? 0 : 1;
}
