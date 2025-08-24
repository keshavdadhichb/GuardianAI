from fastapi import FastAPI, UploadFile, File
from typing import Optional
import numpy as np
import io
from pydub import AudioSegment
import tensorflow as tf
import tensorflow_hub as hub

app = FastAPI()

# --- 1. Hardcode the YAMNet Class Names ---
# This is the official list of 521 sounds YAMNet can recognize.
YAMNET_CLASS_NAMES = [
    'Speech', 'Child speech, kid speaking', 'Conversation', 'Narration, monologue', 'Babbling', 'Speech synthesizer', 'Shout', 'Bellow', 'Whoop', 'Yell', 'Children shouting', 'Screaming', 'Whispering', 'Laughter', 'Baby laughter', 'Giggle', 'Snicker', 'Belly laugh', 'Chuckle, chortle', 'Crying, sobbing', 'Baby cry, infant cry', 'Whimper', 'Wail, moan', 'Sigh', 'Singing', 'Choir', 'Yodeling', 'Chant', 'Mantra', 'Child singing', 'Synthetic singing', 'Rapping', 'Humming', 'Groan', 'Grunt', 'Whistling', 'Breathing', 'Wheeze', 'Snoring', 'Gasp', 'Pant', 'Snort', 'Cough', 'Throat clearing', 'Sneeze', 'Sniff', 'Run', 'Shuffle', 'Walk, footsteps', 'Chewing, mastication', 'Biting', 'Gargling', 'Stomach rumble', 'Burping, eructation', 'Hiccup', 'Fart', 'Hands', 'Finger snapping', 'Clapping', 'Heart sounds, heartbeat', 'Heart murmur', 'Cheering', 'Applause', 'Chatter', 'Crowd', 'Hubbub, speech noise, speech babble', 'Animal', 'Domestic animals, pets', 'Dog', 'Bark', 'Yip', 'Howl', 'Bow-wow', 'Growling', 'Whimper (dog)', 'Cat', 'Purr', 'Meow', 'Hiss', 'Caterwaul', 'Livestock, farm animals, working animals', 'Horse', 'Clip-clop', 'Neigh, whinny', 'Cattle, bovinae', 'Moo', 'Cowbell', 'Pig', 'Oink', 'Goat', 'Bleat', 'Sheep', 'Fowl', 'Chicken, rooster', 'Cluck', 'Crowing, cock-a-doodle-doo', 'Turkey', 'Gobble', 'Duck', 'Quack', 'Goose', 'Honk', 'Wild animals', 'Roaring cats (lions, tigers)', 'Roar', 'Bird', 'Bird vocalization, bird call, bird song', 'Chirp, tweet', 'Squawk', 'Pigeon, dove', 'Coo', 'Crow', 'Caw', 'Owl', 'Hoot', 'Bird flight, flapping wings', 'Canidae, dogs, wolves', 'Rodents, rats, mice', 'Mouse', 'Patter', 'Insect', 'Cricket', 'Mosquito', 'Fly, housefly', 'Buzz', 'Bee, wasp, etc.', 'Frog', 'Croak', 'Snake', 'Rattle', 'Whale vocalization', 'Music', 'Musical instrument', 'Plucked string instrument', 'Guitar', 'Acoustic guitar', 'Steel guitar, slide guitar', 'Electric guitar', 'Distortion', 'Rock music', 'Banjo', 'Sitar', 'Mandolin', 'Zither', 'Ukulele', 'Keyboard (musical)', 'Piano', 'Electric piano', 'Organ', 'Electronic organ', 'Hammond organ', 'Synthesizer', 'Sampler', 'Sequencer', 'Percussion', 'Drum kit', 'Drum machine', 'Drum', 'Snare drum', 'Rimshot', 'Drum roll', 'Bass drum', 'Timpani', 'Tabla', 'Cymbal', 'Hi-hat', 'Wood block', 'Tambourine', 'Rattle (instrument)', 'Maraca', 'Gong', 'Tubular bells', 'Mallet percussion', 'Marimba, xylophone', 'Glockenspiel', 'Vibraphone', 'Steelpan', 'Orchestra', 'Brass instrument', 'French horn', 'Trumpet', 'Trombone', 'Tuba', 'Cornet', 'Fanfare', 'Woodwind instrument', 'Flute', 'Clarinet', 'Saxophone', 'Oboe', 'Bassoon', 'Harp', 'Bell', 'Church bell', 'Jingle bell', 'Bowed string instrument', 'String section', 'Violin, fiddle', 'Pizzicato', 'Cello', 'Double bass', 'Fiddle', 'Harmonica', 'Accordion', 'Bagpipes', 'Didgeridoo', 'Shofar', 'Theremin', 'Singing bowl', 'Scratching (performance technique)', 'Pop music', 'Hip hop music', 'Beatboxing', 'Rock and roll', 'Heavy metal', 'Punk rock', 'Grunge', 'Progressive rock', 'Rockabilly', 'Ska', 'Reggae', 'Country', 'Swing music', 'Bluegrass', 'Funk', 'Folk music', 'Middle Eastern music', 'Jazz', 'Disco', 'Classical music', 'Opera', 'Electronic music', 'House music', 'Techno', 'Dubstep', 'Drum and bass', 'Electronica', 'Electronic dance music', 'Ambient music', 'Trance music', 'Music of Latin America', 'Salsa music', 'Flamenco', 'Blues', 'Music for children', 'New-age music', 'Vocal music', 'A capella', 'Music of Africa', 'Afrobeat', 'Christian music', 'Gospel music', 'Music of Asia', 'Carnatic music', 'Hindustani music', 'Jingle (music)', 'Soundtrack music', 'Film score', 'Video game music', 'Christmas music', 'Dance music', 'Lullaby', 'Wedding music', 'Happy music', 'Sad music', 'Tender music', 'Exciting music', 'Angry music', 'Scary music', 'Wind', 'Rustling leaves', 'Wind noise (microphone)', 'Thunderstorm', 'Thunder', 'Rain', 'Raindrop', 'Rain on surface', 'Water', 'Stream', 'Gurgling', 'Waterfall', 'Ocean', 'Waves, surf', 'Gush', 'Drip', 'Liquid', 'Pour', 'Splash, splish', 'Slosh', 'Squish', 'Dribble', 'Bubbling', 'Tearing', 'Fire', 'Crackle', 'Vehicle', 'Boat, Water vehicle', 'Sailboat, sailing ship', 'Rowboat, canoe, kayak', 'Motorboat', 'Ferry', 'Car', 'Vehicle horn, car horn, honking', 'Toot', 'Car alarm', 'Power windows, electric windows', 'Skidding', 'Tire squeal', 'Car passing by', 'Race car, auto racing', 'Truck', 'Air brake', 'Air horn, truck horn', 'Reversing beeps', 'Ice cream truck, music box', 'Bus', 'Train', 'Train whistle', 'Train horn', 'Railroad car, train wagon', 'Train wheels squealing', 'Subway, metro, underground', 'Aircraft', 'Helicopter', 'Fixed-wing aircraft, airplane', 'Jet engine', 'Propeller, airscrew', 'Bicycle', 'Skateboard', 'Engine', 'Light engine (high frequency)', 'Loud engine (low frequency)', 'Engine accelerating', 'Engine idling', 'Engine knocking', 'Engine starting', 'Chainsaw', 'Tools', 'Power tool', 'Drill', 'Sawing', 'Sanding', 'Hammer', 'Jackhammer', 'Screwdriver', 'Wrench', 'Filing (rasp)', 'Screeching', 'Home appliance', 'Blender', 'Vacuum cleaner', 'Electric shaver, electric razor', 'Toothbrush', 'Electric toothbrush', 'Hair dryer', 'Alarm', 'Siren', 'Civil defense siren', 'Police car (siren)', 'Ambulance (siren)', 'Fire engine, fire truck (siren)', 'Foghorn', 'Whistle', 'Steam whistle', 'Train whistle', 'Buzzer', 'Smoke detector, smoke alarm', 'Fire alarm', 'Burglar alarm', 'Doorbell', 'Clock', 'Tick', 'Tick-tock', 'Ticking', 'Alarm clock', 'Telephone', 'Telephone bell ringing', 'Ringtone', 'Telephone dialing, DTMF', 'Dial tone', 'Busy signal', 'Domestic sounds, home sounds', 'Door', 'Doorbell', 'Door knocker', 'Sliding door', 'Slam', 'Knock', 'Tap', 'Squeak', 'Drawer open or close', 'Window', 'Window blind', 'Dishes, pots, and pans', 'Cutlery, silverware', 'Chopping (food)', 'Frying (food)', 'Microwave oven', 'Water tap, faucet', 'Sink (filling or washing)', 'Bathtub (filling or washing)', 'Toilet flush', 'Zipper (clothing)', 'Keys jangling', 'Coin (dropping)', 'Packing tape, duct tape', 'Scissors', 'Typing', 'Typewriter', 'Computer keyboard', 'Writing', 'Shuffling cards', 'Gunshot, gunfire', 'Explosion', 'Boom', 'Wood', 'Chop', 'Splinter', 'Crack', 'Glass', 'Chink, clink', 'Shatter', 'Breaking', 'Sound effect', 'Pulse', 'Inside, small room', 'Inside, large room or hall', 'Inside, public space', 'Acoustic environment', 'Silence', 'Human group actions', 'Whip', 'Speech jammer', 'Music genre', 'White noise', 'Pink noise', 'Brown noise', 'Throbbing', 'Vibration'
]


# --- 2. Load the Pre-trained YAMNet Model ---
print("Loading YAMNet model...")
yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
print("✅ YAMNet model loaded.")

@app.get("/")
def read_root():
    return {"message": "GuardianAI AI Service is running"}

@app.post("/api/analyze")
async def analyze_media(
    video_file: Optional[UploadFile] = File(None), 
    audio_file: Optional[UploadFile] = File(None)
):
    # --- Hardcoded Video Logic ---
    if video_file:
        print(f"Received video file: {video_file.filename}")
        if "crime" in video_file.filename.lower():
            return {"verdict": "High Priority Alert: Violent Activity Detected in Video."}
        else:
            return {"verdict": "Normal activity detected in video."}

    # --- Real Audio Logic with YAMNet ---
    if audio_file:
        print(f"Received audio file: {audio_file.filename}")
        contents = await audio_file.read()
        try:
            # Use pydub to handle any audio format and resample for YAMNet
            audio = AudioSegment.from_file(io.BytesIO(contents), format="m4a")
            audio = audio.set_frame_rate(16000).set_channels(1)
            # Convert to NumPy array for TensorFlow
            waveform = np.array(audio.get_array_of_samples(), dtype=np.float32) / (2**15)

            # Run the model
            scores, embeddings, spectrogram = yamnet_model(waveform)
            scores = scores.numpy()
            
            # Ensure scores are valid before proceeding
            if scores.size == 0 or scores.shape[1] != len(YAMNET_CLASS_NAMES):
                print("Warning: Model returned invalid scores.")
                return {"verdict": "Could not analyze audio due to invalid model output."}
            
            mean_scores = np.mean(scores, axis=0)

            # Find all detected sounds above a confidence threshold
            detected_sounds = {}
            for i in range(len(mean_scores)):
                if mean_scores[i] > 0.1: # Confidence threshold
                    class_name = YAMNET_CLASS_NAMES[i]
                    detected_sounds[class_name] = round(float(mean_scores[i]), 4)
            
            print(f"Detected sounds: {detected_sounds}")

            # Determine the verdict
            verdict = "Normal activity detected in audio."
            for sound, confidence in detected_sounds.items():
                if sound in ["Screaming", "Yell", "Shout"]:
                    verdict = f"High Priority Alert: {sound} detected (Confidence: {confidence})"
                    break
            
            return {"verdict": verdict}

        except Exception as e:
            print(f"Error processing audio file: {e}")
            return {"verdict": "Error: Could not process audio."}
    
    return {"verdict": "No file received."}