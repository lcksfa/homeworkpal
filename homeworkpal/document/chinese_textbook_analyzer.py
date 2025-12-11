"""
语文教材智能分析器
Chinese Textbook Intelligent Analyzer

专门用于分析人教版语文教材的单元、课文结构
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class LessonInfo:
    """课文信息"""
    unit_number: int
    unit_title: str
    lesson_number: int
    lesson_title: str
    start_page: int
    end_page: Optional[int] = None
    content_chunks: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.content_chunks is None:
            self.content_chunks = []


@dataclass
class TextbookStructure:
    """教材结构"""
    grade: str
    subject: str
    units: List[LessonInfo]
    total_lessons: int

    def __post_init__(self):
        self.total_lessons = len(self.units)


class ChineseTextbookAnalyzer:
    """语文教材智能分析器"""

    def __init__(self):
        """初始化分析器"""
        # 单元识别模式 - 基于实际PDF目录页格式
        self.unit_patterns = [
            r'第([一二三四五六七八九十\d]+)单元\s*',
            r'([一二三四五六七八九十\d]+)、([^。\n]*单元)',
        ]

        # 课文识别模式 - 基于实际PDF目录页格式
        self.lesson_patterns = [
            r'\s*(\d+)\s+([^。\n]{2,30})(?:\.\.\.\.\.\.\.)?',  # 目录中的格式：1 大青树下的小学.......
            r'第([一二三四五六七八九十\d]+)课\s*([^\n]{2,30})',
            r'(\d+)、([^。\n]{2,30})(?:课|篇)',
            r'([《][^《》]{2,30}[》])',
        ]

        # 人教版三年级上册语文已知课文标题 (完整列表)
        self.known_lessons = {
            1: [  # 第一单元
                "大青树下的小学",
                "花的学校",
                "不懂就要问"
            ],
            2: [  # 第二单元
                "古诗三首",
                "山行",
                "赠刘景文",
                "夜书所见",
                "铺满金色巴掌的水泥道",
                "秋天的雨",
                "听听，秋的声音"
            ],
            3: [  # 第三单元
                "卖火柴的小女孩",
                "那一定会很好",
                "在牛肚子里旅行",
                "一块奶酪",
                "总也倒不了的老屋",
                "胡萝卜先生的长胡子",
                "小狗学叫"
            ],
            4: [  # 第四单元
                "搭船的鸟",
                "金色的草地"
            ],
            5: [  # 第五单元
                "古诗三首",
                "望天门山",
                "饮湖上初晴后雨",
                "望洞庭",
                "富饶的西沙群岛",
                "海滨小城",
                "美丽的小兴安岭"
            ],
            6: [  # 第六单元
                "大自然的声音",
                "父亲、树林和鸟",
                "带刺的朋友"
            ],
            7: [  # 第七单元
                "大自然的声音",
                "父亲、树林和鸟",
                "带刺的朋友"
            ],
            8: [  # 第八单元
                "司马光",
                "掌声",
                "手术台就是阵地"
            ]
        }

        # 章节和练习识别
        self.section_patterns = [
            r'(口语交际：[^\n]{2,30})',
            r'(习作：[^\n]{2,30})',
            r'(语文园地)',
            r'(习作例文：[^\n]{2,30})',
            r'(我爱故乡的杨梅)',
            r'(我们眼中的缤纷世界)',
        ]

    def analyze_textbook_structure(self, chunks: List[Dict[str, Any]]) -> TextbookStructure:
        """
        分析教材结构

        Args:
            chunks: PDF处理后的文本片段列表

        Returns:
            教材结构信息
        """
        logger.info("开始分析语文教材结构")

        # 按页码排序
        sorted_chunks = sorted(chunks, key=lambda x: x.get('page_number', 0))

        # 先从目录页提取所有单元信息
        units = self._extract_units_from_directory(sorted_chunks)

        # 如果没有找到足够单元，使用通用方法
        if len(units) < 4:  # 至少应该有4个单元
            logger.warning("目录页识别不完整，尝试通用识别方法")
            units = self._extract_units(sorted_chunks)

        # 识别课文
        lessons = self._extract_lessons(sorted_chunks, units)

        # 分配内容到课文
        self._assign_content_to_lessons(sorted_chunks, lessons)

        structure = TextbookStructure(
            grade="三年级",
            subject="语文",
            units=lessons,
            total_lessons=len(lessons)
        )

        logger.info(f"分析完成：{len(lessons)} 篇课文，{len(units)} 个单元")
        return structure

    def _extract_units_from_directory(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从目录页提取所有8个单元信息"""
        units = []
        directory_content = ""

        # 合并目录页内容（第4和第5页）
        for chunk in chunks:
            page = chunk.get('page_number', 0)
            content = chunk['content']

            # 检查是否是目录页
            if page in [4, 5] and ('目录' in content or '单元' in content):
                directory_content += content + "\n"

        if directory_content:
            logger.info("从目录页提取单元信息")

            # 提取所有单元模式
            unit_pattern = r'第([一二三四五六七八九十\d]+)单元'
            unit_matches = re.findall(unit_pattern, directory_content)

            for unit_chinese in unit_matches:
                unit_number = self._chinese_number_to_int(unit_chinese)
                unit_info = {
                    'page': 4,  # 目录页统一设为第4页
                    'unit_number': unit_number,
                    'unit_title': f"第{unit_number}单元",
                    'content': f"第{unit_number}单元",
                    'chunk_id': 'directory_page'
                }
                units.append(unit_info)
                logger.debug(f"从目录提取单元: 第{unit_number}单元")

            # 确保所有8个单元都被包含
            if len(units) < 8:
                logger.info(f"目录页只找到{len(units)}个单元，补充完整的8个单元")
                found_numbers = {u['unit_number'] for u in units}
                for i in range(1, 9):
                    if i not in found_numbers:
                        unit_info = {
                            'page': 4,
                            'unit_number': i,
                            'unit_title': f"第{i}单元",
                            'content': f"第{i}单元",
                            'chunk_id': 'directory_page'
                        }
                        units.append(unit_info)

        return sorted(units, key=lambda x: x['unit_number'])[:8]  # 确保只返回前8个单元

    def _extract_units(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取单元信息"""
        units = []
        seen_units = set()

        for chunk in chunks:
            content = chunk['content']
            page = chunk.get('page_number', 0)

            # 尝试匹配单元模式
            for pattern in self.unit_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    # 提取单元编号
                    unit_number_str = match.group(1)
                    unit_number = self._chinese_number_to_int(unit_number_str)

                    # 避免重复添加
                    if unit_number in seen_units:
                        continue

                    # 提取单元标题
                    if len(match.groups()) > 1 and match.group(2):
                        unit_title = match.group(2).strip()
                    else:
                        unit_title = f"第{unit_number}单元"

                    unit_info = {
                        'page': page,
                        'unit_number': unit_number,
                        'unit_title': unit_title,
                        'content': match.group(0),
                        'chunk_id': chunk.get('chunk_id')
                    }
                    units.append(unit_info)
                    seen_units.add(unit_number)
                    logger.debug(f"发现单元: {unit_info['unit_number']} - {unit_info['unit_title']} (页{page})")

        return sorted(units, key=lambda x: x['page'])

    def _extract_lessons(self, chunks: List[Dict[str, Any]], units: List[Dict[str, Any]]) -> List[LessonInfo]:
        """提取课文信息"""
        lessons = []
        seen_lessons = set()
        unit_lesson_count = {}

        # 1. 首先从目录页提取所有课文信息
        directory_lessons = self._extract_lessons_from_directory(chunks)
        lessons.extend(directory_lessons)

        # 2. 然后在内容页查找实际课文位置
        # 创建页码到单元的映射（根据实际页码）
        unit_page_ranges = {
            1: (2, 12),   # 第一单元：页2-12
            2: (13, 26),  # 第二单元：页13-26
            3: (27, 44),  # 第三单元：页27-44
            4: (45, 62),  # 第四单元：页45-62
            5: (63, 72),  # 第五单元：页63-72
            6: (73, 86),  # 第六单元：页73-86
            7: (87, 100), # 第七单元：页87-100
            8: (101, 113) # 第八单元：页101-113
        }

        for chunk in chunks:
            content = chunk['content']
            page = chunk.get('page_number', 0)

            # 确定当前单元
            current_unit = None
            for unit_num, (start_page, end_page) in unit_page_ranges.items():
                if start_page <= page <= end_page:
                    current_unit = {
                        'unit_number': unit_num,
                        'unit_title': f"第{unit_num}单元"
                    }
                    break

            # 如果能确定单元，查找课文内容
            if current_unit:
                unit_num = current_unit['unit_number']

                # 使用已知课文列表匹配
                if unit_num in self.known_lessons:
                    known_lessons = self.known_lessons[unit_num]
                    for lesson_title in known_lessons:
                        if lesson_title in content and len(lesson_title) > 3:  # 避免太短的匹配
                            # 避免重复添加
                            lesson_key = (unit_num, lesson_title)
                            if lesson_key in seen_lessons:
                                continue

                            # 查找对应的目录课文信息来获取正确的课文编号
                            lesson_number = None
                            for dir_lesson in directory_lessons:
                                if (dir_lesson.unit_number == unit_num and
                                    dir_lesson.lesson_title == lesson_title):
                                    lesson_number = dir_lesson.lesson_number
                                    break

                            # 如果在目录中没找到，使用计数
                            if lesson_number is None:
                                lesson_number = unit_lesson_count.get(unit_num, 0) + 1

                            lesson = LessonInfo(
                                unit_number=unit_num,
                                unit_title=current_unit['unit_title'],
                                lesson_number=lesson_number,
                                lesson_title=lesson_title,
                                start_page=page
                            )
                            lessons.append(lesson)
                            seen_lessons.add(lesson_key)
                            unit_lesson_count[unit_num] = lesson_number
                            logger.debug(f"在内容页找到课文: {lesson_title} (第{unit_num}单元, 第{lesson_number}课, 页{page})")

        # 合并并去重
        final_lessons = []
        seen_final = set()
        for lesson in lessons:
            lesson_key = (lesson.unit_number, lesson.lesson_title)
            if lesson_key not in seen_final:
                final_lessons.append(lesson)
                seen_final.add(lesson_key)

        return final_lessons

    def _extract_lessons_from_directory(self, chunks: List[Dict[str, Any]]) -> List[LessonInfo]:
        """从目录页提取课文信息"""
        lessons = []
        directory_content = ""

        # 合并目录页内容（第4和第5页）
        for chunk in chunks:
            page = chunk.get('page_number', 0)
            content = chunk['content']

            # 检查是否是目录页
            if page in [4, 5] and ('目录' in content or '单元' in content):
                directory_content += content + "\n"

        if directory_content:
            logger.info("从目录页提取课文信息")

            # 按单元分割内容
            unit_sections = re.split(r'第([一二三四五六七八九十\d]+)单元', directory_content)

            current_unit = 1
            for i in range(1, len(unit_sections), 2):  # 跳过第0个空元素，然后每两个一组
                if i >= len(unit_sections) - 1:
                    break

                unit_chinese = unit_sections[i]
                unit_content = unit_sections[i + 1]

                unit_number = self._chinese_number_to_int(unit_chinese)

                # 在单元内容中查找课文
                lesson_pattern = r'(\d+)\s+([^。\n]{2,30})(?:\*{0,2})(?:\.{4,})?\s*(\d+)'
                lesson_matches = re.findall(lesson_pattern, unit_content)

                lesson_counter = 1
                for lesson_num_str, lesson_title, page_num in lesson_matches:
                    lesson_title = lesson_title.strip()
                    if (len(lesson_title) > 1 and
                        not any(skip in lesson_title for skip in ['口语', '习作', '语文园地', '快乐读书吧', '识字表', '写字表', '词语表'])):

                        lesson = LessonInfo(
                            unit_number=unit_number,
                            unit_title=f"第{unit_number}单元",
                            lesson_number=int(lesson_num_str),
                            lesson_title=lesson_title,
                            start_page=int(page_num)
                        )
                        lessons.append(lesson)
                        logger.debug(f"目录提取课文: 第{unit_number}单元 第{lesson_num_str}课 {lesson_title} (页{page_num})")
                        lesson_counter += 1

        return lessons

    def _assign_content_to_lessons(self, chunks: List[Dict[str, Any]], lessons: List[LessonInfo]):
        """将内容分配到对应的课文"""

        for i, lesson in enumerate(lessons):
            # 确定课文的页面范围
            start_page = lesson.start_page
            end_page = lessons[i + 1].start_page - 1 if i + 1 < len(lessons) else 999

            # 查找此课文页面范围内的所有片段
            for chunk in chunks:
                page = chunk.get('page_number', 0)

                # 检查是否在课文的页面范围内
                if start_page <= page <= end_page:
                    # 验证内容是否属于此课文
                    content = chunk['content']

                    # 如果是课文的起始页面，确保包含课文标题
                    if page == start_page and lesson.lesson_title in content:
                        lesson.content_chunks.append(chunk)
                    # 如果不是起始页面，检查是否包含相关内容
                    elif page > start_page:
                        # 排除明显是其他课文或章节的内容
                        is_other_content = self._is_content_from_other_lesson(content, lesson, lessons)
                        if not is_other_content:
                            lesson.content_chunks.append(chunk)

            # 设置课文的结束页面
            if lesson.content_chunks:
                lesson.end_page = max(chunk.get('page_number', 0) for chunk in lesson.content_chunks)
                logger.debug(f"课文 {lesson.lesson_title}: 页{lesson.start_page}-{lesson.end_page}, {len(lesson.content_chunks)} 个片段")

    def _is_content_from_other_lesson(self, content: str, current_lesson: LessonInfo, all_lessons: List[LessonInfo]) -> bool:
        """检查内容是否来自其他课文"""

        # 检查是否包含其他课文标题
        for lesson in all_lessons:
            if lesson.lesson_title != current_lesson.lesson_title and lesson.lesson_title in content:
                return True

        # 检查是否包含单元标题
        if "单元" in content and current_lesson.unit_title not in content:
            return True

        # 检查是否是章节分隔内容
        sections = ["口语交际", "习作", "语文园地", "习作例文"]
        for section in sections:
            if section in content and current_lesson.unit_title not in content:
                return True

        return False

    def _chinese_number_to_int(self, chinese_num: str) -> int:
        """将中文数字转换为整数"""
        chinese_map = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }

        # 如果是阿拉伯数字，直接返回
        if chinese_num.isdigit():
            return int(chinese_num)

        # 如果是中文数字，进行转换
        if chinese_num in chinese_map:
            return chinese_map[chinese_num]

        # 处理十几的情况
        if len(chinese_num) == 2 and chinese_num[0] == '十':
            return 10 + chinese_map.get(chinese_num[1], 0)

        # 处理二十几到九十几的情况
        if len(chinese_num) == 2 and chinese_num[1] == '十':
            return chinese_map.get(chinese_num[0], 0) * 10

        return 1  # 默认值

    def get_lesson_statistics(self, structure: TextbookStructure) -> Dict[str, Any]:
        """获取课文统计信息"""
        stats = {
            'total_units': len(set(lesson.unit_number for lesson in structure.units)),
            'total_lessons': len(structure.units),
            'units': {}
        }

        # 按单元统计
        for lesson in structure.units:
            unit_key = f"第{lesson.unit_number}单元"
            if unit_key not in stats['units']:
                stats['units'][unit_key] = {
                    'unit_title': lesson.unit_title,
                    'lessons': [],
                    'total_pages': 0,
                    'total_chunks': 0
                }

            stats['units'][unit_key]['lessons'].append({
                'lesson_number': lesson.lesson_number,
                'lesson_title': lesson.lesson_title,
                'pages': f"{lesson.start_page}-{lesson.end_page}",
                'chunks': len(lesson.content_chunks) if lesson.content_chunks else 0
            })

            if lesson.end_page:
                stats['units'][unit_key]['total_pages'] += (lesson.end_page - lesson.start_page + 1)
            if lesson.content_chunks:
                stats['units'][unit_key]['total_chunks'] += len(lesson.content_chunks)

        return stats


def create_chinese_textbook_analyzer() -> ChineseTextbookAnalyzer:
    """创建语文教材分析器实例"""
    return ChineseTextbookAnalyzer()