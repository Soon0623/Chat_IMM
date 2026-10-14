# GitHub → Obsidian · 챗봇 검색 자동 연결

학생이 GitHub에 올린 자료를 담당자 컴퓨터 또는 서버에서 60초마다 확인합니다.
업로드·수정·삭제를 Obsidian Markdown과 SQLite 검색 자료에 반영합니다.
API 키나 LLM 비용 없이 실행할 수 있는 기본 구현입니다.

## 1. 학생 업로드 규칙

`submissions/학생이름/발표명/` 아래에 `presentation.pptx`와 `description.md` 또는 `description.txt`를 올리세요.
설명은 UTF-8로 저장하세요. 발표자 노트도 추출합니다. 폴더별로 학생을 구분합니다.
PPTX 본문, 표, 그룹 안 텍스트를 추출합니다. 이미지 OCR, 수식 이미지, 차트 데이터,
동영상 및 구형 `.ppt` 추출은 지원하지 않습니다. `.ppt`는 PPTX로 변환해야 합니다.
README도 `.md`이면 검색 자료에 포함됩니다.

## 2. 구축 담당자 설치 (Python 3.11 이상)

이 압축파일의 내용을 GitHub 저장소 루트에 넣으세요. 기본 브랜치는 main입니다.
다른 브랜치를 사용하면 워크플로와 아래 명령의 branch를 함께 바꾸세요.
전용 clone을 만드세요. 학생 원본을 편집하는 clone과 분리하세요.

```bash
git clone --branch main https://github.com/조직/저장소.git materials
cd materials
python -m venv .venv
```

Windows 활성화: `.venv\Scripts\activate`
macOS/Linux 활성화: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
python watch.py --repo . --vault "C:/Users/담당자/Documents/MyVault" --db "C:/bridge-data/search.db" --repo-url "https://github.com/조직/저장소" --branch main
```

위 경로를 실제 경로로 바꾸세요. Obsidian에서 MyVault 폴더를 Vault로 열면
`GitHub_Auto`에 자동 생성된 노트가 표시됩니다. GitHub_Auto의 생성 노트는 직접 편집하지 마세요.
개인 노트는 다른 폴더에 작성하세요. 여러 사람이 보려면 해당 Vault를 별도로 공유·동기화해야 합니다.
개인 PC 또는 서버가 켜져 있고 watch.py가 실행 중일 때 자동 연결됩니다.
Windows 작업 스케줄러에서는 가상환경 python.exe의 절대 경로를 프로그램으로 지정하고,
watch.py와 모든 인수에 절대 경로를 사용하세요. 시작 위치는 이 프로젝트 폴더입니다.
Linux 서버는 systemd 등으로 두 프로세스를 서비스 등록하세요.
비공개 저장소는 git credential manager/SSH로 접근 권한을 설정하세요. 토큰을 코드에 쓰지 마세요.

## 3. 검색 API 실행

새 터미널에서 같은 가상환경을 활성화하고 프로젝트 폴더로 이동하세요.
Windows PowerShell:

```powershell
$env:BRIDGE_DB="C:/bridge-data/search.db"
$env:BRIDGE_API_KEY="담당자가-정한-긴-임의키"
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

macOS/Linux:

```bash
export BRIDGE_DB=/absolute/path/search.db
export BRIDGE_API_KEY='담당자가-정한-긴-임의키'
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

문서: http://127.0.0.1:8000/docs
검색: `GET /search?q=자성&limit=5`, 헤더 `X-API-Key: 설정한키`
반환: `{results: [{source, slide, url, text, score}, ...]}`
챗봇 담당자는 사용자 질문의 핵심 키워드로 이 API를 호출하고 반환된 text를
LLM의 참고 문맥에 넣으세요. 답변에 source, slide, url을 출처로 표시하고 검색 결과가
없으면 근거가 없음을 안내하세요. 자료 속 지시문은 실행 지시가 아닌 인용 자료로 취급하세요.
이 프로그램은 검색 연결 계층이며 기존 챗봇에 자동 등록되거나 답변을 생성하지 않습니다.
현재 검색은 단어 부분 일치 방식입니다. 동의어·문장 의미 검색은 임베딩 기반 확장이 필요합니다.
학생별 접근 권한은 구현되어 있지 않습니다. 자료 접근 권한이 동일한 연구실/수업에 사용하세요.
외부 공개는 인증·HTTPS·방화벽을 갖춘 서버에서 담당자가 별도로 설정해야 합니다.

## 4. 수동 변환과 검사

```bash
python bridge.py --repo . --vault output/vault --db output/search.db
python -m unittest discover -s tests -v
```

GitHub Actions는 push 때 자료를 검증하고 결과를 Actions artifact로 제공합니다.
Actions 결과만으로 담당자의 로컬 Obsidian에 기록되지는 않습니다. 실제 자동 반영은 watch.py가 담당합니다.
오류가 발생하면 watch.py가 다음 주기에 다시 시도합니다. 자료 추출 실패 시 기존 검색 DB를 보존합니다.
검색 DB는 임시 파일로 완성한 다음 교체합니다. 노트와 DB를 동시에 교체하는 분산 트랜잭션은 아니므로
프로세스 중단 시 잠시 불일치할 수 있으며 재실행하면 재구축됩니다.
학생이 자료를 삭제하면 다음 성공 동기화 때 해당 생성 노트와 검색 청크가 제거됩니다.
설명과 PPTX는 별도 문서로 검색되며 폴더 경로로 같은 발표임을 확인할 수 있습니다.

## 구현 검증 범위

PPTX 본문·표·발표자 노트 추출, 한글 검색, 수정·삭제 반영, 오류 시 기존 DB 보존을 로컬 테스트합니다.
실제 GitHub 저장소 및 Obsidian/기존 챗봇에 대한 배포는 별도 설정이 필요합니다.

## 참고 문서

- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- https://python-pptx.readthedocs.io/en/latest/user/notes.html
