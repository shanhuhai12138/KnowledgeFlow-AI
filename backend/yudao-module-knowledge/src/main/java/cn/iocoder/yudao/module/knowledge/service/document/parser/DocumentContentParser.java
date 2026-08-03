package cn.iocoder.yudao.module.knowledge.service.document.parser;

import cn.hutool.core.io.IoUtil;
import lombok.extern.slf4j.Slf4j;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.springframework.stereotype.Component;

import java.io.InputStream;

/**
 * 文档文本解析器（T2.5）：将 MinIO 对象解析为全文文本，供 /ai/ingest 分块向量化。
 *
 * 支持：txt/md（UTF-8 直读）、pdf（PDFBox）、docx（Apache POI）
 */
@Slf4j
@Component
public class DocumentContentParser {

    /**
     * 解析文档为全文文本
     *
     * @param input    MinIO 对象流
     * @param fileType 文件类型：pdf/docx/txt/md
     */
    public String parse(InputStream input, String fileType) throws Exception {
        switch (fileType == null ? "" : fileType.toLowerCase()) {
            case "txt":
            case "md":
                return IoUtil.readUtf8(input);
            case "pdf":
                return parsePdf(input);
            case "docx":
                return parseDocx(input);
            default:
                throw new IllegalArgumentException("不支持的解析类型: " + fileType);
        }
    }

    private String parsePdf(InputStream input) throws Exception {
        try (PDDocument document = PDDocument.load(input)) {
            PDFTextStripper stripper = new PDFTextStripper();
            return stripper.getText(document);
        }
    }

    private String parseDocx(InputStream input) throws Exception {
        try (XWPFDocument document = new XWPFDocument(input)) {
            StringBuilder content = new StringBuilder();
            for (XWPFParagraph paragraph : document.getParagraphs()) {
                if (paragraph.getText() != null && !paragraph.getText().isEmpty()) {
                    content.append(paragraph.getText()).append('\n');
                }
            }
            return content.toString();
        }
    }

}
