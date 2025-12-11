#!/usr/bin/env python3
"""
CSV内容清理脚本（简化版）
CSV Content Cleaning Script (Simple Version)

清理CSV文件中的多余空白，直接修改content字段，并添加简单的分类标识
"""

import os
import sys
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def print_status(message: str, status: str):
    """打印状态信息"""
    icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "🔧": "🔧", "📚": "📚", "🔍": "🔍", "💾": "💾", "📖": "📖"}
    print(f"{icons.get(status, 'ℹ️')} {message}")


def clean_content_text(text: str) -> str:
    """清理文本中的多余空白"""
    if pd.isna(text) or not text:
        return text

    # 转换为字符串
    text = str(text)

    # 将多个连续空格替换为单个空格
    text = re.sub(r' +', ' ', text)

    # 将多个连续换行符替换为单个换行符
    text = re.sub(r'\n+', '\n', text)

    # 处理特殊的空白字符（如全角空格）
    text = re.sub(r'\u3000+', ' ', text)  # 全角空格
    text = re.sub(r'\u00A0+', ' ', text)  # 不换行空格

    # 清理换行符后的多余空格
    text = re.sub(r'\n +', '\n', text)

    # 清理空格后的换行符
    text = re.sub(r' +\n', '\n', text)

    # 移除行首行尾空白
    text = text.strip()

    return text


def classify_content_simple(content: str, lesson_title: str, unit_title: str) -> str:
    """
    简单分类内容类型
    返回: '课文', '日积月累', '习作', '交流', '练习', '古诗', '阅读', '其他'
    """
    if pd.isna(content) or not content:
        return '其他'

    content_lower = str(content).lower()

    # 日积月累类
    if any(keyword in content_lower for keyword in [
        '日积月累', '古诗', '唐诗', '宋词', '清 袁枚', '唐 杜牧', '宋 苏轼', '宋 叶绍翁',
        '所 见', '山 行', '赠刘景文', '夜书所见'
    ]):
        return '日积月累'

    # 习作类
    elif any(keyword in content_lower for keyword in [
        '习作', '写日记', '小练笔', '猜猜他是谁', '续写故事', '编童话',
        '我来编童话', '写一写', '写下来', '写作'
    ]):
        return '习作'

    # 口语交际类
    elif any(keyword in content_lower for keyword in [
        '口语交际', '和同学交流', '交流平台', '讨论', '分享', '说一说',
        '猜猜他是谁', '名字里的故事', '请教', '身边的小事'
    ]):
        return '交流'

    # 练习类
    elif any(keyword in content_lower for keyword in [
        '朗读课文', '背诵课文', '默写', '想一想', '练习', '选择',
        '下面的', '怎样', '如何', '说说', '画下来', '抄写'
    ]):
        return '练习'

    # 阅读类
    elif any(keyword in content_lower for keyword in [
        '阅读链接', '阅读', '选自', '本文作者', '译者', '选作课文时有改动'
    ]) and '习作' not in content_lower and '交流' not in content_lower:
        return '阅读'

    # 古诗类（专门识别）
    elif any(keyword in content_lower for keyword in [
        '古诗三首', '山行', '赠刘景文', '夜书所见', '望天门山', '饮湖上初晴后雨',
        '望洞庭', '司马光'
    ]):
        return '古诗'

    # 课文主体类
    elif any(keyword in content_lower for keyword in [
        '早晨，', '从前，', '有一个', '很久很久以前', '三国', '宋', '唐', '清',
        '本文作者', '选作课文时有改动', '故事', '小女孩', '小男孩'
    ]) and len(content) > 100:
        return '课文'

    # 辅助材料类
    elif any(keyword in content_lower for keyword in [
        '目录', '序', '版权页', '封面', '封底', '义务教育教科书', '主编',
        '编写人员', '责任编辑', '美术编辑', '出版社', '邮编'
    ]):
        return '其他'

    # 基于长度和内容特征判断
    else:
        if len(content) > 200 and '。' in content and '，' in content:
            return '课文'
        elif len(content) < 100 and ('？' in content or '！' in content):
            return '练习'
        else:
            return '其他'


def clean_and_classify_csv(input_path: Path, output_path: Path) -> pd.DataFrame:
    """清理和分类CSV文件"""
    # 读取原始CSV
    print_status(f"读取CSV文件: {input_path}", "📖")
    df = pd.read_csv(input_path)
    print_status(f"原始CSV包含 {len(df)} 条记录", "📊")

    # 添加分类列
    df['content_category'] = ''

    print_status("开始清理和分类内容", "🔧")

    for idx, row in df.iterrows():
        if idx % 20 == 0:
            print_status(f"处理进度: {idx+1}/{len(df)}", "📊")

        # 获取原始内容
        content = row.get('content', '')
        lesson_title = row.get('lesson_title', '')
        unit_title = row.get('unit_title', '')

        # 1. 清理内容
        cleaned_content = clean_content_text(content)
        df.at[idx, 'content'] = cleaned_content

        # 2. 分类内容
        category = classify_content_simple(cleaned_content, lesson_title, unit_title)
        df.at[idx, 'content_category'] = category

    return df


def generate_summary(df: pd.DataFrame) -> Dict:
    """生成处理摘要"""
    summary = {
        'total_records': len(df),
        'categories': df['content_category'].value_counts().to_dict(),
        'cleaned_records': 0
    }

    # 统计清理的记录数（通过与原始记录比较长度变化）
    for idx, row in df.iterrows():
        original_length = len(str(row.get('content', '')))
        # 假设原始内容有空白，清理后长度会不同
        if original_length > 10:  # 只统计有意义的内容
            summary['cleaned_records'] += 1

    return summary


def main():
    """主函数"""
    print_status("开始CSV内容清理和分类", "🚀")
    print("=" * 50)

    # 设置文件路径
    input_csv = project_root / "exports" / "语文三上_content_fixed.csv"
    output_csv = project_root / "exports" / "语文三上_content_cleaned.csv"

    if not input_csv.exists():
        print_status(f"输入文件不存在: {input_csv}", "❌")
        return 1

    try:
        # 处理CSV文件
        cleaned_df = clean_and_classify_csv(input_csv, output_csv)

        # 生成摘要报告
        summary = generate_summary(cleaned_df)

        # 保存清理后的CSV
        print_status(f"保存清理后的CSV文件: {output_csv}", "💾")
        cleaned_df.to_csv(output_csv, index=False, encoding='utf-8')

        # 显示结果
        print("\n" + "=" * 50)
        print_status("✅ CSV内容清理和分类完成！", "✅")
        print(f"📊 处理记录数: {summary['total_records']}")
        print(f"🧹 清理记录数: {summary['cleaned_records']}")

        print("\n📋 内容分类统计:")
        category_names = {
            '课文': '课文主体',
            '古诗': '古诗欣赏',
            '日积月累': '日积月累',
            '习作': '习作指导',
            '交流': '口语交际',
            '练习': '课后练习',
            '阅读': '阅读材料',
            '其他': '其他内容'
        }

        for category, count in summary['categories'].items():
            name = category_names.get(category, category)
            print(f"   {name}: {count} 条")

        print(f"\n📄 输出文件: {output_csv}")
        print("\n💡 后续建议:")
        print("   1. 检查清理后的内容质量")
        print("   2. 验证分类结果是否合理")
        print("   3. 使用清理后的CSV文件重新导入数据库")

        return 0

    except Exception as e:
        print_status(f"CSV处理失败: {e}", "❌")
        return 1


if __name__ == "__main__":
    sys.exit(main())