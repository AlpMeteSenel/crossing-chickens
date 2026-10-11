import base64,json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import cv2,numpy as np
from local_recording import JpegAVI,RollingCapture,AnnotatedRecording,buffer_status,export_clean,list_clips,download_path,render_annotation

def jpeg(frame):return cv2.imencode('.jpg',frame)[1].tobytes()

class Tests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.image=np.full((64,96,3),80,np.uint8)
    def tearDown(self):self.tmp.cleanup()
    def test_avi_decodes_and_preserves_capture_time_gap(self):
        path=self.root/'video.avi';writer=JpegAVI(path,96,64)
        writer.add(jpeg(self.image),100);writer.add(jpeg(self.image+40),100.3);writer.close()
        self.assertEqual(len(writer.index),4);self.assertEqual(writer.info()['source_frames'],2)
        cap=cv2.VideoCapture(str(path));self.assertTrue(cap.isOpened());self.assertEqual(cap.get(cv2.CAP_PROP_FRAME_COUNT),4)
        decoded=[]
        while True:
            ok,image=cap.read()
            if not ok:break
            decoded.append(image)
        cap.release();self.assertEqual(len(decoded),4)
        self.assertLess(decoded[0].mean(),decoded[-1].mean());self.assertEqual(decoded[1].shape,(64,96,3))
    def test_rolling_retention_export_and_timestamps(self):
        recorder=RollingCapture(self.root)
        try:
            now=time.time()
            for i in range(171):recorder.consume(self.image,now-17+i*.1)
            status=buffer_status(self.root)
            self.assertTrue(status['ready']);self.assertLessEqual(status['buffered_seconds'],15)
            self.assertLessEqual(len(list(recorder.directory.glob('*.jpg'))),151)
            clip=export_clean(self.root);self.assertEqual(clip['kind'],'clean');self.assertLessEqual(clip['duration_seconds'],15)
            cap=cv2.VideoCapture(str(download_path(self.root,clip['name'])));self.assertTrue(cap.isOpened());self.assertTrue(cap.read()[0]);cap.release()
            sidecar=download_path(self.root,clip['name'].replace('.avi','.json'));self.assertEqual(json.loads(sidecar.read_text())['source_frames'],clip['source_frames'])
            self.assertEqual(len(list_clips(self.root)),1)
            self.assertFalse(list((self.root/'recordings/clips').glob('.snapshot-*')))
        finally:recorder.close()
    def test_stale_buffer_refuses_save_and_rotation_clears_old_frames(self):
        recorder=RollingCapture(self.root)
        try:
            recorder.consume(self.image,time.time()-5)
            self.assertFalse(buffer_status(self.root)['ready'])
            with self.assertRaises(ValueError):export_clean(self.root)
            (self.root/'control.json').write_text('{"camera_rotation":90}')
            recorder.consume(self.image,time.time());self.assertEqual(len(recorder.records),1)
            self.assertEqual((recorder.records[0]['w'],recorder.records[0]['h']),(64,96))
        finally:recorder.close()
    def test_bounded_nonblocking_capture_queue(self):
        recorder=RollingCapture(self.root);recorder.close()
        start=time.monotonic()
        for i in range(100):recorder.offer(self.image,start+i)
        self.assertLessEqual(recorder.queue.qsize(),2);self.assertGreater(recorder.dropped,0)
    def test_sampling_deadline_avoids_halving_13fps_sensor_to_6fps(self):
        recorder=RollingCapture(self.root);recorder.close()
        start=time.monotonic();accepted=0
        for i in range(130):
            recorder.offer(self.image,start+i/13)
            while not recorder.queue.empty():recorder.queue.get_nowait();recorder.queue.task_done();accepted+=1
        self.assertGreaterEqual(accepted,99);self.assertLessEqual(accepted,101)

    def test_annotated_recording_has_boxes_and_valid_download(self):
        recorder=AnnotatedRecording(self.root);recorder.start();now=time.time()
        vision={'profile':{},'tracks':[{'cls':'person','id':12,'conf':.88,'box':[.2,.2,.8,.8],'speed_kmh':4.2}]}
        camera={'frame':base64.b64encode(jpeg(self.image)).decode(),'capture_ts':now-.2,'source_kind':'live','camera_rotation':0}
        recorder.feed(camera,vision);camera['capture_ts']=now-.05;recorder.feed(camera,vision)
        recorder.stop();recorder.close();self.assertFalse(recorder.status()['active']);self.assertFalse(recorder.status()['finishing'])
        clips=list_clips(self.root);self.assertEqual(len(clips),1);self.assertEqual(clips[0]['kind'],'yolo')
        cap=cv2.VideoCapture(str(download_path(self.root,clips[0]['name'])));ok,frame=cap.read();cap.release();self.assertTrue(ok)
        self.assertGreater(np.abs(frame.astype(float)-self.image).mean(),5)
        with self.assertRaises(ValueError):download_path(self.root,'../../control.json')
        with self.assertRaises(ValueError):download_path(self.root,'other.avi')
    def test_clean_encode_does_not_mutate_detector_frame(self):
        frame=self.image.copy();original=frame.copy();recorder=RollingCapture(self.root)
        try:recorder.consume(frame,time.time());np.testing.assert_array_equal(frame,original)
        finally:recorder.close()
    def test_render_contains_tracked_object_without_touching_other_pixels(self):
        frame=np.zeros((200,300,3),np.uint8)
        render_annotation(frame,{'profile':{},'tracks':[{'cls':'car','id':3,'conf':.91,'box':[.3,.4,.7,.8],'speed_kmh':12.5}]})
        self.assertTrue(frame[80,90].any());self.assertFalse(frame[199,299].any())

if __name__=='__main__':unittest.main()
