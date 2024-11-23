import re
import numpy as np
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Embedding, LSTM, Dense
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle
from konlpy.tag import Okt

# 전처리 도구 및 불용어 정의
okt = Okt()
stopwords = ['은', '는', '이', '가', '을', '를', '들', '에', '와', '한', '거', 
             '하다', '있다', '되다', '그', '저', '이렇다', '그렇다', '어떻다', 
             '등', '또', '보다', '때문', '만', '더', '이것', '저것', '같다', '같이']

# 텍스트 전처리 함수
def preprocess_text(text):
    text = re.sub(r'[^가-힣\s]', '', text)  # 한글 및 공백 제외 문자 제거
    tokens = okt.morphs(text, stem=True)
    tokens = [word for word in tokens if word not in stopwords]
    return ' '.join(tokens)

# 감정 분석 함수
def predict_sentiment(review_text):
    # 모델 및 토크나이저 로드
    model = load_model('models/lstm_model.h5')
    with open('models/tokenizer.pickle', 'rb') as handle:
        tokenizer = pickle.load(handle)

    # 리뷰 전처리 및 예측 수행
    preprocessed_text = preprocess_text(review_text)
    sequence = tokenizer.texts_to_sequences([preprocessed_text])
    padded_sequence = pad_sequences(sequence, maxlen=100)
    prediction = model.predict(padded_sequence)[0][0]
    sentiment = "positive" if prediction > 0.5 else "negative"
    return sentiment

if __name__ == "__main__":
    # 데이터 불러오기
    train_data_path = 'data/ratings_train.txt'
    with open(train_data_path, 'r', encoding='utf-8') as f:
        data = f.readlines()

    texts, labels = [], []
    for i, line in enumerate(data):
        # 첫 줄이 헤더일 수 있으므로 건너뜁니다.
        if i == 0 and 'label' in line:
            continue
        parts = line.strip().split('\t')
        if len(parts) == 3:  # ID, text, label 형식일 경우
            _, text, label = parts
            texts.append(preprocess_text(text))
            labels.append(int(label))

    # 텍스트 토크나이저 및 패딩
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(texts)
    sequences = tokenizer.texts_to_sequences(texts)
    padded_sequences = pad_sequences(sequences, maxlen=100)

    # 모델 학습을 위한 설정
    embedding_dim = 100
    max_words = len(tokenizer.word_index) + 1

    model = Sequential()
    model.add(Embedding(input_dim=max_words, output_dim=embedding_dim, input_length=100))
    model.add(LSTM(128))
    model.add(Dense(1, activation='sigmoid'))

    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.summary()

    # 데이터 학습
    labels = np.array(labels)
    model.fit(padded_sequences, labels, epochs=5, batch_size=64, validation_split=0.2)

    # 모델 및 토크나이저 저장
    model.save('models/lstm_model.h5')
    with open('models/tokenizer.pickle', 'wb') as handle:
        pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

    print("모델 및 토크나이저 저장 완료")
