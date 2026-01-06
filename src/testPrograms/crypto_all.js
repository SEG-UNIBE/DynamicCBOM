// crypto_demo.js
// Comprehensive demo of Node's crypto: asymmetric, symmetric, hashing, HMAC, KDF

const crypto = require('crypto');

// ---------- Utility helpers ----------

function toHex(buf) {
  return buf.toString('hex');
}

// ---------- Asymmetric: RSA key pair, encrypt/decrypt, sign/verify ----------

function generateRsaKeyPair() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
    modulusLength: 2048, // bits
    publicKeyEncoding: {
      type: 'spki',
      format: 'pem',
    },
    privateKeyEncoding: {
      type: 'pkcs8',
      format: 'pem',
    },
  });
  return { publicKey, privateKey };
}

function rsaEncrypt(publicKeyPem, plaintext) {
  const ciphertext = crypto.publicEncrypt(
    {
      key: publicKeyPem,
      padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
      oaepHash: 'sha256',
    },
    Buffer.from(plaintext, 'utf8'),
  );
  return ciphertext;
}

function rsaDecrypt(privateKeyPem, ciphertext) {
  const plaintextBuf = crypto.privateDecrypt(
    {
      key: privateKeyPem,
      padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
      oaepHash: 'sha256',
    },
    ciphertext,
  );
  return plaintextBuf.toString('utf8');
}

function rsaSign(privateKeyPem, message) {
  const signature = crypto.sign(
    'sha256',
    Buffer.from(message, 'utf8'),
    {
      key: privateKeyPem,
      padding: crypto.constants.RSA_PKCS1_PSS_PADDING,
      saltLength: crypto.constants.RSA_PSS_SALTLEN_DIGEST,
    },
  );
  return signature;
}

function rsaVerify(publicKeyPem, message, signature) {
  return crypto.verify(
    'sha256',
    Buffer.from(message, 'utf8'),
    {
      key: publicKeyPem,
      padding: crypto.constants.RSA_PKCS1_PSS_PADDING,
      saltLength: crypto.constants.RSA_PSS_SALTLEN_DIGEST,
    },
    signature,
  );
}

// ---------- Asymmetric: EC (ECDSA) sign/verify ----------

function generateEcKeyPair() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ec', {
    namedCurve: 'prime256v1', // aka P-256
    publicKeyEncoding: {
      type: 'spki',
      format: 'pem',
    },
    privateKeyEncoding: {
      type: 'pkcs8',
      format: 'pem',
    },
  });
  return { publicKey, privateKey };
}

function ecdsaSign(privateKeyPem, message) {
  const sign = crypto.createSign('sha256');
  sign.update(message);
  sign.end();
  return sign.sign(privateKeyPem);
}

function ecdsaVerify(publicKeyPem, message, signature) {
  const verify = crypto.createVerify('sha256');
  verify.update(message);
  verify.end();
  return verify.verify(publicKeyPem, signature);
}

// ---------- Symmetric: AES-256-GCM (AEAD) ----------

function aesGcmEncrypt(plaintext, aadString = null) {
  const key = crypto.randomBytes(32); // 256-bit key
  const iv = crypto.randomBytes(12);  // 96-bit nonce recommended for GCM
  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);

  if (aadString) {
    cipher.setAAD(Buffer.from(aadString, 'utf8'));
  }

  const ciphertext = Buffer.concat([
    cipher.update(plaintext, 'utf8'),
    cipher.final(),
  ]);
  const authTag = cipher.getAuthTag();

  return {
    key,
    iv,
    ciphertext,
    authTag,
    aad: aadString ? Buffer.from(aadString, 'utf8') : null,
  };
}

function aesGcmDecrypt({ key, iv, ciphertext, authTag, aad }) {
  const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);

  if (aad) {
    decipher.setAAD(aad);
  }

  decipher.setAuthTag(authTag);

  const plaintextBuf = Buffer.concat([
    decipher.update(ciphertext),
    decipher.final(),
  ]);

  return plaintextBuf.toString('utf8');
}

// ---------- Symmetric: AES-256-CBC ----------

function aesCbcEncrypt(plaintext) {
  const key = crypto.randomBytes(32); // 256-bit
  const iv = crypto.randomBytes(16);  // 128-bit block size
  const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);

  const ciphertext = Buffer.concat([
    cipher.update(plaintext, 'utf8'),
    cipher.final(),
  ]);

  return { key, iv, ciphertext };
}

function aesCbcDecrypt({ key, iv, ciphertext }) {
  const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);

  const plaintextBuf = Buffer.concat([
    decipher.update(ciphertext),
    decipher.final(),
  ]);

  return plaintextBuf.toString('utf8');
}

// ---------- Hashing: SHA-256 (single and streaming) ----------

function hashSha256(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

function hashSha256Streaming(chunks) {
  const hash = crypto.createHash('sha256');
  for (const chunk of chunks) {
    hash.update(chunk);
  }
  return hash.digest('hex');
}

// ---------- HMAC: HMAC-SHA256 ----------

function hmacSha256(key, data) {
  return crypto.createHmac('sha256', key).update(data).digest('hex');
}

// ---------- KDF: scryptSync / pbkdf2Sync ----------

function deriveKeyWithScrypt(password, salt = crypto.randomBytes(16), keyLen = 32) {
  const key = crypto.scryptSync(password, salt, keyLen);
  return { key, salt };
}

function deriveKeyWithPbkdf2(password, salt = crypto.randomBytes(16), keyLen = 32) {
  const iterations = 100_000;
  const digest = 'sha256';
  const key = crypto.pbkdf2Sync(password, salt, iterations, keyLen, digest);
  return { key, salt, iterations, digest };
}

// ---------- Demo runner ----------

function main() {
  const message = 'Dynamic CBOM + Node.js crypto demo 🚀';
  console.log('Original message:', message);
  console.log('---');

  // Asymmetric: RSA
  console.log('=== Asymmetric: RSA ===');
  const rsaKeys = generateRsaKeyPair();
  console.log('RSA public key (PEM snippet):', rsaKeys.publicKey.split('\n')[0], '...');
  console.log('RSA private key (PEM snippet):', rsaKeys.privateKey.split('\n')[0], '...');

  const rsaCiphertext = rsaEncrypt(rsaKeys.publicKey, message);
  console.log('RSA-OAEP ciphertext (hex):', toHex(rsaCiphertext));

  const rsaPlain = rsaDecrypt(rsaKeys.privateKey, rsaCiphertext);
  console.log('RSA-OAEP decrypted:', rsaPlain);

  const rsaSignature = rsaSign(rsaKeys.privateKey, message);
  console.log('RSA-PSS signature (hex):', toHex(rsaSignature));

  const rsaOk = rsaVerify(rsaKeys.publicKey, message, rsaSignature);
  console.log('RSA-PSS signature valid?', rsaOk);
  console.log('---');

  // Asymmetric: ECDSA
  console.log('=== Asymmetric: ECDSA (P-256) ===');
  const ecKeys = generateEcKeyPair();
  console.log('EC public key (PEM snippet):', ecKeys.publicKey.split('\n')[0], '...');
  console.log('EC private key (PEM snippet):', ecKeys.privateKey.split('\n')[0], '...');

  const ecSig = ecdsaSign(ecKeys.privateKey, message);
  console.log('ECDSA signature (hex):', toHex(ecSig));

  const ecOk = ecdsaVerify(ecKeys.publicKey, message, ecSig);
  console.log('ECDSA signature valid?', ecOk);
  console.log('---');

  // Symmetric: AES-GCM
  console.log('=== Symmetric: AES-256-GCM (AEAD) ===');
  const aad = 'demo-associated-data';
  const gcmResult = aesGcmEncrypt(message, aad);
  console.log('AES-GCM key (hex):', toHex(gcmResult.key));
  console.log('AES-GCM iv (hex):', toHex(gcmResult.iv));
  console.log('AES-GCM ciphertext (hex):', toHex(gcmResult.ciphertext));
  console.log('AES-GCM authTag (hex):', toHex(gcmResult.authTag));

  const gcmPlain = aesGcmDecrypt(gcmResult);
  console.log('AES-GCM decrypted:', gcmPlain);
  console.log('---');

  // Symmetric: AES-CBC
  console.log('=== Symmetric: AES-256-CBC ===');
  const cbcResult = aesCbcEncrypt(message);
  console.log('AES-CBC key (hex):', toHex(cbcResult.key));
  console.log('AES-CBC iv (hex):', toHex(cbcResult.iv));
  console.log('AES-CBC ciphertext (hex):', toHex(cbcResult.ciphertext));

  const cbcPlain = aesCbcDecrypt(cbcResult);
  console.log('AES-CBC decrypted:', cbcPlain);
  console.log('---');

  // Hashing
  console.log('=== Hashing: SHA-256 ===');
  const hash1 = hashSha256(message);
  console.log('SHA-256 (single update):', hash1);

  const hash2 = hashSha256Streaming(['Dynamic ', 'CBOM ', '+ ', 'Node.js crypto demo 🚀']);
  console.log('SHA-256 (streaming updates):', hash2);
  console.log('Hashes equal?', hash1 === hash2);
  console.log('---');

  // HMAC
  console.log('=== HMAC: HMAC-SHA256 ===');
  const hmacKey = crypto.randomBytes(32);
  const hmac = hmacSha256(hmacKey, message);
  console.log('HMAC key (hex):', toHex(hmacKey));
  console.log('HMAC-SHA256:', hmac);
  console.log('---');

  // KDFs
  console.log('=== KDF: scrypt ===');
  const scryptResult = deriveKeyWithScrypt('correct horse battery staple');
  console.log('scrypt salt (hex):', toHex(scryptResult.salt));
  console.log('scrypt key  (hex):', toHex(scryptResult.key));

  console.log('=== KDF: PBKDF2 ===');
  const pbkdf2Result = deriveKeyWithPbkdf2('correct horse battery staple');
  console.log('pbkdf2 salt (hex):', toHex(pbkdf2Result.salt));
  console.log('pbkdf2 key  (hex):', toHex(pbkdf2Result.key));
  console.log('pbkdf2 iterations:', pbkdf2Result.iterations);
  console.log('pbkdf2 digest:', pbkdf2Result.digest);

  console.log('--- Demo finished ---');
}

if (require.main === module) {
  main();
}

// Optionally export functions if you want to import this as a library.
module.exports = {
  generateRsaKeyPair,
  rsaEncrypt,
  rsaDecrypt,
  rsaSign,
  rsaVerify,
  generateEcKeyPair,
  ecdsaSign,
  ecdsaVerify,
  aesGcmEncrypt,
  aesGcmDecrypt,
  aesCbcEncrypt,
  aesCbcDecrypt,
  hashSha256,
  hashSha256Streaming,
  hmacSha256,
  deriveKeyWithScrypt,
  deriveKeyWithPbkdf2,
};
