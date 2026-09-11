import sys
from pathlib import Path
import unittest
import tempfile
from decimal import Decimal as D

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from episode_video import align_text, caption_chunks, int_chinese, normal, shot_timeline, timeline_path, validate_v2, full_typography
from narrated_video import font_index

class EpisodeTests(unittest.TestCase):
    def test_portable_timeline_resolves_paths_from_edition_directory(self):
        directory=Path('/restored/project/outputs/coffee-shop/short')
        self.assertEqual(timeline_path('../../../examples/video/coffee-shop/short.json',directory),Path('/restored/project/examples/video/coffee-shop/short.json'))
        self.assertEqual(timeline_path('audio/S01.wav',directory),directory/'audio/S01.wav')
        self.assertEqual(timeline_path('/original/audio.wav',directory),Path('/original/audio.wav'))

    @unittest.skipUnless(Path('/System/Library/Fonts/STHeiti Medium.ttc').exists(), 'macOS font regression')
    def test_chinese_collection_uses_sc_glyphs_instead_of_tc_default(self):
        from PIL import ImageFont
        path='/System/Library/Fonts/STHeiti Medium.ttc'
        chosen=ImageFont.truetype(path,72,index=font_index({'font':path}))
        old=ImageFont.truetype(path,72,index=0)
        self.assertEqual(chosen.getname()[0],'Heiti SC')
        # Same U+5F84 text produced the wrong regional glyph in the old renderer.
        self.assertNotEqual(bytes(chosen.getmask('径')),bytes(old.getmask('径')))

    def test_structural_check_ignores_runtime_but_checks_authored_files(self):
        from quick_validate import Validator
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            dependency=root/'.venv/lib/vendor.py';dependency.parent.mkdir(parents=True)
            dependency.write_text('TO'+'DO')
            validator=Validator(root);validator.validate_no_draft_markers()
            self.assertEqual(validator.errors,[])
            (root/'authored.py').write_text('TO'+'DO')
            validator.validate_no_draft_markers()
            self.assertEqual(len(validator.errors),1)

    def test_captions_preserve_all_narration_and_stay_readable(self):
        text='洗一次十二元，烘一次十元。假设每十筒洗衣，平均带来六次烘干。'
        parts=caption_chunks(text)
        self.assertEqual(''.join(parts),text)
        self.assertTrue(all(len(p)<=24 for p in parts))

    def test_recognized_numbers_match_spoken_chinese(self):
        self.assertEqual(normal('全年 57,600 元。'),normal('全年五万七千六百元。'))
        self.assertEqual(normal('57600元'),normal('五万七千六百元'))
        self.assertEqual(int_chinese(10080),'一万零八十')
        self.assertEqual(int_chinese(12),'十二')

    def test_alignment_uses_measured_word_times(self):
        text='机器自己转。手机自己收钱。'
        words=[{'word':'机器自己转','start':.2,'end':2.0},{'word':'手机自己收钱','start':3.1,'end':5.4}]
        captions,ratio,_=align_text(text,words,5.8)
        self.assertEqual(captions[0]['end'],3.1)
        self.assertEqual(captions[1]['start'],3.1)
        self.assertEqual(captions[-1]['end'],5.8)
        self.assertEqual(ratio,1)

    def test_unrelated_speech_is_rejected(self):
        with self.assertRaises(ValueError):
            align_text('洗衣店收入是多少',[{'word':'完全无关故事','start':0,'end':3}],3)

    def test_repeated_narration_is_rejected(self):
        with self.assertRaises(ValueError):
            align_text('一年剩多少。',[{'word':'一年剩多少一年剩多少','start':0,'end':5}],5)

    def test_split_numeric_words_form_one_amount(self):
        cap,ratio,_=align_text('一年五万七千六百元。',[
            {'word':'一年','start':0,'end':.5},
            {'word':'57','start':.5,'end':1},
            {'word':'600','start':1,'end':1.5},
            {'word':'元','start':1.5,'end':2}],2.2)
        self.assertEqual(ratio,1)
        self.assertEqual(cap[0]['text'],'一年五万七千六百元。')

    def test_shots_cover_audio_without_gaps_or_extra_frames(self):
        blocks=[{'id':'a','start_frame':0,'frames':101,'shots':[{'layout':'scene'},{'layout':'table'}]},
                {'id':'b','start_frame':101,'frames':88,'shots':[{'layout':'scene'}]}]
        shots=shot_timeline(blocks)
        self.assertEqual(shots[0]['start_frame'],0)
        self.assertEqual(shots[-1]['end_frame'],189)
        self.assertTrue(all(a['end_frame']==b['start_frame'] for a,b in zip(shots,shots[1:])))

    def test_render_validation_rejects_missing_images(self):
        m={'schema_version':2,'blocks':[{'id':'a','text':'正文','shots':[{'layout':'scene','image':'absent.png'}]}]}
        validate_v2(m,Path('/missing'),images=False)
        with self.assertRaises(ValueError):validate_v2(m,Path('/missing'),images=True)

    def test_explicit_cuts_follow_narration_and_cover_the_block(self):
        shots=shot_timeline([{'id':'a','start_frame':150,'frames':270,'shots':[
            {'layout':'full','at_seconds':0},{'layout':'full','at_seconds':1.74},{'layout':'full','at_seconds':6.2}]}])
        self.assertEqual([(s['start_frame'],s['end_frame']) for s in shots],[(150,202),(202,336),(336,420)])

    def test_invalid_or_collapsed_explicit_cuts_fail_before_rendering(self):
        for times in ([1,2],[0,2,1],[0,9],[0,.001],[0,float('nan')],[0,-1]):
            with self.subTest(times=times),self.assertRaises(ValueError):
                shot_timeline([{'id':'a','start_frame':0,'frames':270,'shots':[{'at_seconds':t} for t in times]}])
        with self.assertRaises(ValueError):
            shot_timeline([{'id':'a','start_frame':0,'frames':270,'shots':[{'at_seconds':0},{}]}])

    @unittest.skipUnless(Path('/System/Library/Fonts/STHeiti Medium.ttc').exists(), 'macOS font regression')
    def test_full_frame_overlay_leaves_artwork_visible_and_rejects_clipped_text(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'layer.png'
            full_typography({'disclosure':'演示假设'},{'labels':[{'text':'12 元','x':.2,'y':.5,'size':96}]},'洗一次十二元。',output)
            with Image.open(output) as im:
                self.assertEqual(im.getpixel((1500,400))[3],0)
                self.assertGreater(im.getpixel((960,987))[3],0)
            with self.assertRaises(ValueError):
                full_typography({}, {'labels':[{'text':'这个文字不能超出画面','x':.99,'y':.5,'size':96}]},'',output)

    def test_wash_dry_ledger_and_sensitivities(self):
        fixed=72000+48000+18000+42000
        def profit(q,price=D(12),attach=D('.6')):
            contribution=price-D(3)+attach*(D(10)-D(3))
            return contribution*q*360-fixed
        self.assertEqual(profit(50),57600)
        self.assertEqual(profit(40),10080)
        self.assertEqual(profit(30),-37440)
        self.assertEqual(profit(50,price=D(10)),21600)
        self.assertEqual(profit(50,attach=D('.4')),32400)
        self.assertEqual(D(18)-D('4.8'),D('13.2'))
        self.assertLess(profit(37),0)
        self.assertGreaterEqual(profit(38),0)

if __name__=='__main__':unittest.main()
