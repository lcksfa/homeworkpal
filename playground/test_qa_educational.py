#!/usr/bin/env python3
"""
作业搭子问答系统教育场景测试
Test QA System for Educational Scenarios
"""

import asyncio
import time
import json
from homeworkpal.rag.qa_service import QAService, QARequest


async def test_educational_qa():
    """测试教育场景问答功能"""

    print("🌟 作业搭子问答系统教育场景测试")
    print("=" * 50)

    # 初始化问答服务
    qa_service = QAService()

    # 测试问题列表（适合三年级学生）
    test_questions = [
        {
            "question": "周长是什么",
            "subject": "数学",
            "grade": "三年级",
            "description": "数学概念理解测试"
        },
        {
            "question": "怎么写好作文的开头",
            "subject": "语文",
            "grade": "三年级",
            "description": "语文写作指导测试"
        },
        {
            "question": "如何描写美丽的景色",
            "subject": "语文",
            "grade": "三年级",
            "description": "写作技巧指导测试"
        },
        {
            "question": "什么是比喻句",
            "subject": "语文",
            "grade": "三年级",
            "description": "修辞手法学习测试"
        }
    ]

    results = []

    for i, test_case in enumerate(test_questions, 1):
        print(f"\n📝 测试 {i}: {test_case['description']}")
        print(f"问题: {test_case['question']}")
        print(f"学科: {test_case['subject']} | 年级: {test_case['grade']}")
        print("-" * 50)

        # 创建问答请求
        request = QARequest(
            question=test_case["question"],
            subject=test_case["subject"],
            grade=test_case["grade"],
            temperature=0.7,
            max_tokens=800
        )

        try:
            # 执行问答
            start_time = time.time()
            response = await qa_service.ask_question(request)
            end_time = time.time()

            # 显示结果
            print(f"✅ 回答生成成功 (耗时: {response.response_time:.2f}秒)")
            print(f"📚 使用教材上下文: {'是' if response.context_used else '否'}")
            print(f"📖 参考来源数量: {len(response.sources)}")

            print(f"\n👩‍🏫 老师的回答:")
            print(response.answer)

            if response.sources:
                print(f"\n📚 教材参考:")
                for j, source in enumerate(response.sources[:2], 1):  # 只显示前2个来源
                    print(f"  来源 {j}: {source.get('source_file', '未知文件')} "
                          f"(第{source.get('page_number', '?')}页) "
                          f"相似度: {source.get('score', 0):.3f}")

            # 评估结果
            evaluation = evaluate_response(response, test_case)
            print(f"\n📊 质量评估:")
            print(f"  教师语形: {'✅' if evaluation['teacher_tone'] else '❌'}")
            print(f"  鼓励性: {'✅' if evaluation['encouraging'] else '❌'}")
            print(f"  年龄适配: {'✅' if evaluation['age_appropriate'] else '❌'}")
            print(f"  长度合适: {'✅' if evaluation['good_length'] else '❌'}")
            print(f"  综合评分: {evaluation['overall_score']}/10")

            results.append({
                'test_case': test_case,
                'response_time': response.response_time,
                'context_used': response.context_used,
                'sources_count': len(response.sources),
                'answer_length': len(response.answer),
                'evaluation': evaluation
            })

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append({
                'test_case': test_case,
                'error': str(e)
            })

        print("\n" + "=" * 80)

    # 生成测试报告
    generate_test_report(results)
    print("\n🎉 测试完成！")


def evaluate_response(response, test_case):
    """评估回答质量"""
    evaluation = {
        'teacher_tone': False,
        'encouraging': False,
        'age_appropriate': False,
        'good_length': False,
        'overall_score': 0
    }

    answer = response.answer.lower()

    # 检查教师语形
    teacher_words = ['小朋友', '老师', '你', '我们', '宝贝']
    evaluation['teacher_tone'] = any(word in answer for word in teacher_words)

    # 检查鼓励性
    encouraging_words = ['加油', '继续', '很棒', '不错', '相信', '一定能']
    evaluation['encouraging'] = any(word in answer for word in encouraging_words)

    # 检查年龄适配（避免复杂词汇）
    complex_words = ['抽象', '理论', '概念', '定义', '分析', '综合']
    has_complex = any(word in answer for word in complex_words)
    evaluation['age_appropriate'] = not has_complex or answer.count('比如') > 0  # 如果有复杂词但举例了也算合适

    # 检查长度合适
    length = len(response.answer)
    evaluation['good_length'] = 100 <= length <= 800  # 适合三年级学生阅读的长度

    # 计算综合评分
    score = 0
    if evaluation['teacher_tone']:
        score += 2.5
    if evaluation['encouraging']:
        score += 2.5
    if evaluation['age_appropriate']:
        score += 2.5
    if evaluation['good_length']:
        score += 2.5

    evaluation['overall_score'] = score

    return evaluation


def generate_test_report(results):
    """生成测试报告"""
    print("📊 测试报告摘要")
    print("=" * 30)

    successful_tests = [r for r in results if 'error' not in r]
    failed_tests = [r for r in results if 'error' in r]

    print(f"总测试数: {len(results)}")
    print(f"成功测试: {len(successful_tests)}")
    print(f"失败测试: {len(failed_tests)}")

    if successful_tests:
        avg_response_time = sum(r['response_time'] for r in successful_tests) / len(successful_tests)
        avg_sources_count = sum(r['sources_count'] for r in successful_tests) / len(successful_tests)
        avg_score = sum(r['evaluation']['overall_score'] for r in successful_tests) / len(successful_tests)

        print(f"\n📈 性能指标:")
        print(f"  平均响应时间: {avg_response_time:.2f}秒")
        print(f"  平均参考来源: {avg_sources_count:.1f}个")
        print(f"  平均质量评分: {avg_score:.1f}/10")

        print(f"\n🎯 质量分析:")
        teacher_tone_count = sum(1 for r in successful_tests if r['evaluation']['teacher_tone'])
        encouraging_count = sum(1 for r in successful_tests if r['evaluation']['encouraging'])
        age_appropriate_count = sum(1 for r in successful_tests if r['evaluation']['age_appropriate'])
        good_length_count = sum(1 for r in successful_tests if r['evaluation']['good_length'])

        print(f"  教师语形: {teacher_tone_count}/{len(successful_tests)} ✅")
        print(f"  鼓励性: {encouraging_count}/{len(successful_tests)} ✅")
        print(f"  年龄适配: {age_appropriate_count}/{len(successful_tests)} ✅")
        print(f"  长度合适: {good_length_count}/{len(successful_tests)} ✅")

    if failed_tests:
        print(f"\n❌ 失败原因:")
        for test in failed_tests:
            print(f"  {test['test_case']['question']}: {test['error']}")


if __name__ == "__main__":
    asyncio.run(test_educational_qa())