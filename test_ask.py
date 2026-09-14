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


if __name__ == "__main__":
    unittest.main()
