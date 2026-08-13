package cn.knowledgeflow.module.knowledge.framework.aes;

import lombok.extern.slf4j.Slf4j;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.concurrent.ThreadLocalRandom;

/**
 * AES 加解密工具（CBC/PKCS5Padding，T7 API Key 存储）
 *
 * 密钥派生：CONFIG_SECRET → SHA-256 取前 16 字节；IV 固定 16 字节（演示/单租户场景）。
 * 生产环境建议升级为随机 IV 前置存储 + KMS 管理密钥。
 */
@Slf4j
public class AesUtil {

    private static final String ALGORITHM = "AES/CBC/PKCS5Padding";
    private static final byte[] IV = new byte[16]; // 全 0 IV（演示场景）

    private static volatile String secret;

    /**
     * 获取（或初始化）加密密钥：优先环境变量 CONFIG_SECRET；缺省生成随机密钥并打印一次
     */
    public static String getSecret() {
        if (secret == null) {
            synchronized (AesUtil.class) {
                if (secret == null) {
                    String fromEnv = System.getenv("CONFIG_SECRET");
                    if (fromEnv != null && !fromEnv.isBlank()) {
                        secret = fromEnv;
                    } else {
                        secret = generateRandomSecret();
                        // 仅打印一次，提示部署者保存（开源/演示友好）
                        log.warn("[AesUtil][未配置 CONFIG_SECRET 环境变量，已生成随机密钥（重启后失效）请保存：{}]", secret);
                    }
                }
            }
        }
        return secret;
    }

    public static String encrypt(String plainText) {
        try {
            SecretKeySpec key = deriveKey(getSecret());
            Cipher cipher = Cipher.getInstance(ALGORITHM);
            cipher.init(Cipher.ENCRYPT_MODE, key, new IvParameterSpec(IV));
            byte[] encrypted = cipher.doFinal(plainText.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(encrypted);
        } catch (Exception e) {
            throw new IllegalStateException("AES 加密失败", e);
        }
    }

    public static String decrypt(String cipherText) {
        try {
            SecretKeySpec key = deriveKey(getSecret());
            Cipher cipher = Cipher.getInstance(ALGORITHM);
            cipher.init(Cipher.DECRYPT_MODE, key, new IvParameterSpec(IV));
            byte[] decrypted = cipher.doFinal(Base64.getDecoder().decode(cipherText));
            return new String(decrypted, StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new IllegalStateException("AES 解密失败", e);
        }
    }

    private static SecretKeySpec deriveKey(String secret) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(secret.getBytes(StandardCharsets.UTF_8));
        byte[] keyBytes = new byte[16];
        System.arraycopy(hash, 0, keyBytes, 0, 16);
        return new SecretKeySpec(keyBytes, "AES");
    }

    private static String generateRandomSecret() {
        byte[] bytes = new byte[24];
        ThreadLocalRandom.current().nextBytes(bytes);
        return Base64.getEncoder().encodeToString(bytes);
    }

    /**
     * 掩码：sk-****后4位（key 永不明文返回）
     */
    public static String mask(String apiKey) {
        if (apiKey == null || apiKey.length() < 8) {
            return apiKey == null ? null : apiKey.substring(0, 1) + "****";
        }
        return apiKey.substring(0, Math.min(apiKey.length(), 5)) + "****" + apiKey.substring(apiKey.length() - 4);
    }

}
