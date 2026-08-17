package cn.knowledgeflow.module.knowledge.service.document;

import cn.knowledgeflow.module.knowledge.dal.dataobject.document.DocumentDO;
import cn.knowledgeflow.module.knowledge.dal.mysql.document.DocumentMapper;
import cn.knowledgeflow.module.knowledge.enums.document.DocumentStatusEnum;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * 文档 Service 单元测试
 *
 * @author KnowledgeFlow
 */
@ExtendWith(MockitoExtension.class)
class DocumentServiceImplTest {

    @Mock
    private DocumentMapper documentMapper;

    @InjectMocks
    private DocumentServiceImpl documentService;

    @Test
    void testDocumentStatusEnum() {
        assertEquals("pending", DocumentStatusEnum.PENDING.getStatus());
        assertEquals("processing", DocumentStatusEnum.PROCESSING.getStatus());
        assertEquals("processed", DocumentStatusEnum.PROCESSED.getStatus());
        assertEquals("failed", DocumentStatusEnum.FAILED.getStatus());
    }

    @Test
    void testDocumentStatusFromName() {
        assertEquals(DocumentStatusEnum.PENDING, DocumentStatusEnum.fromName("pending"));
        assertEquals(DocumentStatusEnum.PROCESSING, DocumentStatusEnum.fromName("processing"));
        assertEquals(DocumentStatusEnum.PROCESSED, DocumentStatusEnum.fromName("processed"));
        assertEquals(DocumentStatusEnum.FAILED, DocumentStatusEnum.fromName("failed"));
    }

    @Test
    void testDocumentStatusIsTerminal() {
        assertFalse(DocumentStatusEnum.PENDING.isTerminal());
        assertFalse(DocumentStatusEnum.PROCESSING.isTerminal());
        assertTrue(DocumentStatusEnum.PROCESSED.isTerminal());
        assertTrue(DocumentStatusEnum.FAILED.isTerminal());
    }
}
