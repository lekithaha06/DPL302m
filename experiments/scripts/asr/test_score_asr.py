"""Fixture toán học, không phải kết quả mô hình hoặc dữ liệu test Task2."""
import unittest, unicodedata as ud
from score_asr import normalize, score, without_tone

class ScoreTests(unittest.TestCase):
    def test_counts_and_deletion(self):
        s=score('tôi đang học','tôi học')
        self.assertEqual(s['word_counts'],{'S':0,'D':1,'I':0,'H':2,'N':3})
        self.assertAlmostEqual(s['WER_percent'],100/3)
    def test_tone_and_letter(self):
        s=score('má','mà')
        self.assertEqual(s['tone_only_substitutions'],1)
        self.assertEqual(score('mơ','mo')['tone_only_substitutions'],0)
        self.assertNotEqual(without_tone('đá'),without_tone('da'))
    def test_unicode_and_normalization(self):
        self.assertEqual(normalize(ud.normalize('NFD','TÔI, HỌC! 25%')), 'tôi học 25')
        self.assertEqual(score('hòa','hoà')['WER_percent'],100)
    def test_empty_prediction(self):
        self.assertEqual(score('tôi học','')['word_counts']['D'],2)
        with self.assertRaises(ValueError): score('!!!','tôi')
    def test_wer_above_100(self):
        self.assertEqual(score('a','a b c')['WER_percent'],200)
    def test_cer_spaces_excluded(self):
        s=score('học sinh','họcsinh')
        self.assertEqual(s['CER_percent'],0)
        self.assertGreater(s['WER_percent'],0)
    def test_numbers_preserved(self):
        self.assertEqual(normalize('hai mươi sáu'),'hai mươi sáu')
        self.assertEqual(normalize('26'),'26')
        self.assertEqual(score('hai mươi sáu','26')['WER_percent'],100)

if __name__=='__main__': unittest.main()
