"""
中文文本处理器
Chinese Text Processor for Homework Pal

专门处理语文教材文本的预处理和向量化优化
"""

import re
import hashlib
import logging
from typing import List, Dict, Any, Tuple
from homeworkpal.llm.siliconflow import SiliconFlowEmbeddingModel
import time

logger = logging.getLogger(__name__)


class ChineseTextProcessor:
    """中文文本专用处理器"""

    def __init__(self, embedding_model: SiliconFlowEmbeddingModel):
        """
        初始化中文文本处理器

        Args:
            embedding_model: 向量化模型实例
        """
        self.embedding_model = embedding_model

        # 常见的拼音到汉字映射表（基于小学语文教材）
        self.pinyin_to_hanzi = {
            # 常见单字拼音（基于小学语文三上教材）
            'huK': '呼', 'chSng': '唱', 'jK': '就', 'shuō': '说', 'de': '的', 'le': '了',
            'ma': '吗', 'ne': '呢', 'ba': '吧', 'hěn': '很', 'hǎo': '好', 'shì': '是',
            'yǒu': '有', 'wǒ': '我', 'nǐ': '你', 'tā': '他', 'zhè': '这', 'nà': '那',
            'zheng': '正', 'zài': '在', 'dōu': '都', 'yě': '也', 'bù': '不', 'kě': '可',
            'yǐ': '以', 'hé': '和', 'gěn': '跟', 'yǔ': '与', 'yī': '一', 'èr': '二',
            'sān': '三', 'sì': '四', 'wǔ': '五', 'liù': '六', 'qī': '七', 'bā': '八',
            'jiǔ': '九', 'shí': '十', 'nián': '年', 'yuè': '月', 'rì': '日', 'tiān': '天',

            # 语文教材常见词汇
            'xué': '学', 'xiào': '校', 'jiā': '家', 'mén': '门', 'fáng': '房', 'shū': '书',
            'běn': '本', 'bǐ': '笔', 'zì': '字', 'cí': '词', 'jù': '句', 'duàn': '段',
            'kè': '课', 'wén': '文', 'dú': '读', 'xiě': '写', 'zuò': '做', 'huà': '话',
            'tīng': '听', 'kàn': '看', 'xiǎng': '想', 'sī': '思', 'wèn': '问', 'dá': '答',
            'jiāo': '教', 'yù': '育', 'yǎng': '养', 'xí': '习', 'liàn': '练', 'yóu': '游',
            'xì': '戏', 'wán': '玩', 'lè': '乐', 'qì': '气', 'qíng': '情', 'gǎn': '感',
            'jué': '觉', 'zhī': '知', 'dào': '道', 'lǐ': '理', 'yì': '义', 'guān': '关',
            'yú': '于', 'cóng': '从', 'dào': '到', 'wèi': '为',

            # 动词
            'qǐ': '起', 'zuò': '坐', 'zǒu': '走', 'pǎo': '跑', 'tiào': '跳', 'chī': '吃',
            'hē': '喝', 'shuì': '睡', 'zuò': '做', 'shuō': '说', 'xiào': '笑', 'kū': '哭',
            'kàn': '看', 'tīng': '听', 'xiě': '写', 'dú': '读', 'xiǎng': '想', 'jì': '记',
            'wàng': '忘', 'zhǎo': '找', 'děng': '等', 'bāng': '帮', 'jiào': '叫', 'huà': '画',

            # 形容词
            'hǎo': '好', 'huài': '坏', 'dà': '大', 'xiǎo': '小', 'cháng': '长', 'duǎn': '短',
            'gāo': '高', 'ǎi': '矮', 'pàng': '胖', 'shòu': '瘦', 'měi': '美', 'chǒu': '丑',
            'kuài': '快', 'màn': '慢', 'xīn': '新', 'jiù': '旧', 'duō': '多', 'shǎo': '少',
            'lè': '乐', 'kǔ': '苦', 'tián': '甜', 'suān': '酸', 'là': '辣', 'xián': '咸',

            # 名词
            'fù': '父', 'mǔ': '母', 'gē': '哥', 'jiě': '姐', 'dì': '弟', 'mèi': '妹',
            'shù': '树', 'huā': '花', 'cǎo': '草', 'niǎo': '鸟', 'yú': '鱼', 'mǎ': '马',
            'niú': '牛', 'yáng': '羊', 'gǒu': '狗', 'māo': '猫', 'jī': '鸡', 'yā': '鸭',
            'shān': '山', 'shuǐ': '水', 'tiān': '天', 'dì': '地', 'rì': '日', 'yuè': '月',
            'xīng': '星', 'yún': '云', 'fēng': '风', 'yǔ': '雨', 'xuě': '雪', 'diàn': '电',
        }

    def preprocess_chinese_text_for_embedding(self, text: str) -> str:
        """
        为向量化预处理中文文本

        Args:
            text: 原始文本

        Returns:
            预处理后的文本
        """
        if not text:
            return text

        # 0. 修复拼音识别错误（最优先）
        text = self._fix_pinyin_errors(text)

        # 1. 清理特殊字符和噪音
        text = re.sub(r'\s+', ' ', text)  # 合并多余空白
        text = re.sub(r'\n+', ' ', text)  # 合并换行符

        # 2. 保留中文核心内容（中文字符、标点、数字）
        text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\s，。！？；：""''（）【】《》0-9一二三四五六七八九十]', '', text)

        # 3. 标点符号标准化
        text = text.replace(',', '，').replace('.', '。').replace('!', '！')
        text = text.replace('?', '？').replace(':', '：').replace(';', '；')

        # 4. 移除页码、章节标记等噪音
        text = re.sub(r'\b\d+\s*页\b', '', text)
        text = re.sub(r'\b第\s*\d+\s*课\b', ' 课文 ', text)  # 保留标记但简化
        text = re.sub(r'\b第\s*\d+\s*单元\b', ' 单元 ', text)

        # 5. 移除重复标点
        text = re.sub(r'([。！？]){2,}', r'\1', text)
        text = re.sub(r'([，]){2,}', r'\1', text)

        # 6. 移除过短的无意义片段
        lines = [line.strip() for line in text.split(' ') if line.strip()]
        meaningful_lines = [line for line in lines if len(line) >= 3]

        if not meaningful_lines:
            return ""

        return ' '.join(meaningful_lines).strip()

    def _fix_pinyin_errors(self, text: str) -> str:
        """
        修复PDF解析中的拼音识别错误

        Args:
            text: 原始文本

        Returns:
            修复后的文本
        """
        if not text:
            return text

        # 1. 直接替换常见的拼音错误
        for pinyin, hanzi in self.pinyin_to_hanzi.items():
            # 使用词边界确保只替换独立的拼音
            pattern = rf'(?<![\w@.]){re.escape(pinyin)}(?![\w@.])'
            text = re.sub(pattern, hanzi, text)

        # 2. 修复中文-拼音-中文混合模式
        def fix_middle_pinyin(match):
            prefix, pinyin_part, suffix = match.groups()
            # 查找最匹配的拼音
            pinyin_lower = pinyin_part.lower()
            if pinyin_lower in self.pinyin_to_hanzi:
                return prefix + self.pinyin_to_hanzi[pinyin_lower] + suffix
            return prefix + pinyin_part + suffix

        # 匹配中文-字母-中文模式
        text = re.sub(r'([\u4e00-\u9fff])([a-zA-Z]{1,4})([\u4e00-\u9fff])', fix_middle_pinyin, text)

        # 3. 修复连续大写字母的拼音（如 huK -> 呼）
        def fix_capitalized_pinyin(match):
            pinyin_part = match.group(1)
            # 尝试各种可能的修复
            possible_fixes = [
                pinyin_part.lower(),           # 全部小写
                pinyin_part[:-1].lower(),      # 去掉最后一位大写
                pinyin_part[0].lower() + pinyin_part[1:],  # 首字母小写
            ]

            for fix in possible_fixes:
                if fix in self.pinyin_to_hanzi:
                    return self.pinyin_to_hanzi[fix]

            return pinyin_part

        # 匹配可能的错误拼音模式（如 huK, chSng, jK）
        text = re.sub(r'\b([a-zA-Z]{2,6})\b(?=[\u4e00-\u9fff\s])', fix_capitalized_pinyin, text)

        # 4. 修复常见的编码错误
        encoding_fixes = {
            'ï¼š': '：',
            'ï¼Œ': '，',
            'ï¼›': '？',
            'ï¼': '。',
            'â€': '"',
            'â€': '"',
            'â€¦': '…',
        }

        for wrong, correct in encoding_fixes.items():
            text = text.replace(wrong, correct)

        return text

    def extract_text_hash(self, text: str) -> str:
        """
        生成文本内容的MD5哈希值，用于去重

        Args:
            text: 文本内容

        Returns:
            MD5哈希字符串
        """
        if not text:
            return ""

        # 预处理后再计算哈希
        processed_text = self.preprocess_chinese_text_for_embedding(text)
        return hashlib.md5(processed_text.encode('utf-8')).hexdigest()

    def assess_embedding_quality(self, text: str) -> Dict[str, Any]:
        """
        评估文本是否适合向量化

        Args:
            text: 文本内容

        Returns:
            质量评估结果
        """
        if not text:
            return {'is_suitable': False, 'score': 0.0, 'reason': '文本为空'}

        score = 0.0
        reasons = []

        # 1. 文本长度检查
        length = len(text)
        if length < 20:
            score -= 0.5
            reasons.append('文本过短')
        elif length < 50:
            score -= 0.2
            reasons.append('文本较短')
        elif length > 1000:
            score -= 0.1
            reasons.append('文本较长')
        else:
            score += 0.3

        # 2. 中文内容比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        if chinese_chars == 0:
            score -= 0.8
            reasons.append('无中文字符')
        else:
            chinese_ratio = chinese_chars / length
            score += chinese_ratio * 0.4

        # 3. 教育内容关键词
        education_keywords = [
            '课文', '生字', '词语', '练习', '阅读', '写作', '口语', '交际',
            '拼音', '识字', '写字', '古诗', '学习', '理解', '背诵',
            '例句', '造句', '近义词', '反义词', '意思', '解释'
        ]

        keyword_count = sum(1 for keyword in education_keywords if keyword in text)
        if keyword_count > 0:
            score += min(keyword_count * 0.1, 0.5)

        # 4. 结构化内容
        if re.search(r'[《].*[》]', text):  # 书名号
            score += 0.2
        if re.search(r'^\d+[[、.]', text, re.MULTILINE):  # 编号
            score += 0.1

        # 5. 噪音检测
        noise_indicators = [
            r'^\d+$',  # 纯数字
            r'^[\s\-]*$',  # 纯空格或横线
        ]

        for pattern in noise_indicators:
            if re.match(pattern, text):
                score -= 0.6
                reasons.append('包含噪音内容')
                break

        final_score = max(0.0, min(1.0, score))
        is_suitable = final_score > 0.4

        return {
            'is_suitable': is_suitable,
            'score': final_score,
            'reason': ', '.join(reasons) if reasons else '质量良好',
            'length': length,
            'chinese_chars': chinese_chars,
            'chinese_ratio': chinese_ratio / length if length > 0 else 0,
            'keyword_count': keyword_count
        }

    def batch_vectorize_with_quality_control(
        self,
        text_chunks: List[str],
        batch_size: int = 5,
        max_retries: int = 3,
        quality_threshold: float = 0.4
    ) -> Tuple[List[List[float]], List[Dict[str, Any]]]:
        """
        批量向量化，包含质量控制

        Args:
            text_chunks: 文本片段列表
            batch_size: 批处理大小
            max_retries: 最大重试次数
            quality_threshold: 质量阈值

        Returns:
            (向量列表, 质量评估列表)
        """
        logger.info(f"开始批处理向量化，总共 {len(text_chunks)} 个片段")

        # 1. 质量预筛选
        quality_results = []
        suitable_chunks = []
        suitable_indices = []

        for i, chunk in enumerate(text_chunks):
            quality = self.assess_embedding_quality(chunk)
            quality_results.append(quality)

            if quality['is_suitable']:
                suitable_chunks.append(chunk)
                suitable_indices.append(i)
            else:
                logger.debug(f"跳过低质量片段 {i}: {quality['reason']}")

        logger.info(f"质量筛选: {len(suitable_chunks)}/{len(text_chunks)} 个片段通过")

        # 2. 文本预处理
        processed_chunks = []
        for chunk in suitable_chunks:
            processed = self.preprocess_chinese_text_for_embedding(chunk)
            if processed:  # 确保预处理后不为空
                processed_chunks.append(processed)

        logger.info(f"预处理完成: {len(processed_chunks)} 个有效片段")

        # 3. 批量向量化
        all_embeddings = []
        processed_count = 0

        for i in range(0, len(processed_chunks), batch_size):
            batch = processed_chunks[i:i + batch_size]
            batch_indices = suitable_indices[i:i + batch_size]

            retry_count = 0
            batch_success = False

            while not batch_success and retry_count < max_retries:
                try:
                    logger.debug(f"处理批次 {i//batch_size + 1}/{(len(processed_chunks)-1)//batch_size + 1}")

                    # 调用向量化API
                    embeddings = self.embedding_model.embed_documents(batch)

                    # 验证向量维度
                    if embeddings and len(embeddings[0]) == 1024:  # BGE-M3应该是1024维
                        all_embeddings.extend(embeddings)
                        batch_success = True
                        processed_count += len(batch)

                        # 添加延迟避免API限制
                        time.sleep(0.5)
                    else:
                        logger.warning(f"向量维度异常: {len(embeddings[0]) if embeddings else 'None'}")

                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = retry_count * 2  # 指数退避
                        logger.warning(f"批次处理失败，{wait_time}秒后重试 (第{retry_count}次): {e}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"批次处理最终失败: {e}")
                        # 为失败的批次添加空向量
                        all_embeddings.extend([[0.0] * 1024] * len(batch))

        logger.info(f"向量化完成: {processed_count} 个片段成功")

        # 4. 结果整合（为被过滤的片段添加空向量）
        final_embeddings = []
        final_quality = []

        for i, original_chunk in enumerate(text_chunks):
            if i in suitable_indices:
                # 找到对应的嵌入向量
                idx = suitable_indices.index(i)
                if idx < len(all_embeddings):
                    final_embeddings.append(all_embeddings[idx])
                else:
                    final_embeddings.append([0.0] * 1024)  # 安全默认值
                final_quality.append(quality_results[i])
            else:
                # 被过滤的片段
                final_embeddings.append([0.0] * 1024)
                final_quality.append(quality_results[i])

        return final_embeddings, final_quality

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        获取处理器统计信息

        Returns:
            统计信息字典
        """
        return {
            'embedding_model': type(self.embedding_model).__name__,
            'supports_batch': True,
            'vector_dimension': 1024,
            'quality_threshold': 0.4,
            'default_batch_size': 5,
            'max_retries': 3
        }


def create_chinese_text_processor(embedding_model: SiliconFlowEmbeddingModel) -> ChineseTextProcessor:
    """
    创建中文文本处理器的工厂函数

    Args:
        embedding_model: 向量化模型实例

    Returns:
        中文文本处理器实例
    """
    return ChineseTextProcessor(embedding_model)