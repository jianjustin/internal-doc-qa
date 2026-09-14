#!/usr/bin/env python3
import unittest

from ask import DOCS_DIR, answer


class AskTests(unittest.TestCase):
    def test_hits_cite_source(self):
        text = answer("一线城市住宿上限是多少", DOCS_DIR)
        self.assertIn("差旅报销制度.md", text)
        self.assertIn("600", text)
        self.assertNotIn("拒绝", text)

    def test_missing_doc_refuses(self):
        text = answer("今年公司股价是多少", DOCS_DIR)
        self.assertTrue(text.startswith("拒绝"))
        self.assertNotIn("股价", text)

    def test_leave_policy_cites_file(self):
        text = answer("年假最多能结转几天", DOCS_DIR)
        self.assertIn("请假制度.md", text)
        self.assertIn("2 天", text)

    def test_paraphrase_still_cites_hotel_cap(self):
        text = answer("去上海出差宾馆一晚最多能报多少", DOCS_DIR)
        self.assertIn("差旅报销制度.md", text)
        self.assertIn("600", text)
        self.assertNotIn("拒绝", text)

    def test_out_of_table_paraphrase_still_cites_hotel_cap(self):
        text = answer("去魔都出差住旅店一晚顶格能花多少", DOCS_DIR)
        self.assertIn("差旅报销制度.md", text)
        self.assertIn("600", text)
        self.assertNotIn("拒绝", text)

    def test_leave_paraphrase_does_not_dump_other_leave_types(self):
        text = answer("去年没休完的假明年还能留几天", DOCS_DIR)
        self.assertIn("请假制度.md", text)
        self.assertIn("年假", text)
        self.assertIn("2 天", text)
        self.assertNotIn("病假", text)
        self.assertNotIn("事假", text)
        self.assertNotIn("拒绝", text)

    def test_two_part_question_cites_both_passages(self):
        text = answer("实习生出差要谁批，回来几日内报销", DOCS_DIR)
        self.assertIn("直属经理", text)
        self.assertIn("10 个工作日", text)
        self.assertNotIn("拒绝", text)
        self.assertNotIn("病假", text)

    def test_one_clause_two_topics_cites_hotel_and_train(self):
        text = answer("一线住一晚再加高铁二等座怎么报", DOCS_DIR)
        self.assertIn("600", text)
        self.assertIn("二等座", text)
        self.assertNotIn("拒绝", text)
        self.assertNotIn("病假", text)
        self.assertNotIn("其他城市", text)
        self.assertNotIn("市内交通", text)
        self.assertNotIn("机票：经济舱", text)

    def test_says_amount_not_written_when_policy_has_no_number(self):
        text = answer("超标那晚我自己要掏多少", DOCS_DIR)
        self.assertIn("个人承担", text)
        self.assertIn("没写", text)
        self.assertNotIn("拒绝", text)
        self.assertNotIn("600", text)

    def test_overage_with_night_price_uses_policy_caps(self):
        text = answer("如果住一晚468，超标那晚我自己要掏多少", DOCS_DIR)
        self.assertIn("个人承担", text)
        self.assertIn("600", text)
        self.assertIn("400", text)
        self.assertIn("68", text)
        self.assertNotIn("拒绝", text)
        self.assertNotIn("没写", text)

    def test_speaks_cap_in_a_sentence_before_citation(self):
        text = answer("一线城市住宿上限是多少", DOCS_DIR)
        spoken = text.splitlines()[1]
        self.assertIn("600", spoken)
        self.assertIn("上限", spoken)
        self.assertNotIn("出处", spoken)
        self.assertNotIn("原文", spoken)
        self.assertIn("差旅报销制度.md", text)


if __name__ == "__main__":
    unittest.main()
