# JobFit Implementation Plan

## Phase 1: Core File Parsing ✅ CURRENT PHASE
**Goal:** Read CV files (PDF and DOCX) and extract text

### Tasks:
- ✅ 1.1 Create `src/services/file_parser.py`
  - ✅ Function to read PDF files and extract text
  - ✅Function to read DOCX files and extract text
  - ✅Function to detect file type and call correct parser
- ✅1.2 Test with sample PDF resume
- ✅ 1.3 Test with sample DOCX resume

---

## Phase 2: AI Analysis Service
**Goal:** Send CV + Job Description to OpenAI and get analysis

### Tasks:
- [ ] 2.1 Create `src/services/ai_analyzer.py`
  - [ ] Function to build the prompt (CV text + job description)
  - [ ] Function to call OpenAI API
  - [ ] Function to parse AI response
- [ ] 2.2 Define what analysis we want:
  - [ ] Layout/formatting check
  - [ ] Content completeness check
  - [ ] Job requirement matching
  - [ ] Improvement suggestions
- [ ] 2.3 Test with real CV and job description

---

## Phase 3: Data Models
**Goal:** Define the structure of our data

### Tasks:
- [ ] 3.1 Create `src/models/schemas.py`
  - [ ] CVAnalysisRequest (input: file + job description)
  - [ ] CVAnalysisResponse (output: score, suggestions, etc.)
  - [ ] User model (if needed)
- [ ] 3.2 Create `src/models/database.py`
  - [ ] Database connection setup
  - [ ] Table definitions (users, analyses, etc.)

---

## Phase 4: API Endpoints
**Goal:** Create web endpoints users can call

### Tasks:
- [ ] 4.1 Create `src/api/routes.py`
  - [ ] POST /analyze - upload CV and get analysis
  - [ ] GET /history - get past analyses (optional)
- [ ] 4.2 Update `src/main.py` to run FastAPI server
- [ ] 4.3 Test endpoints with Postman or curl

---

## Phase 5: Frontend (Basic)
**Goal:** Simple web page to upload files

### Tasks:
- [ ] 5.1 Create `src/static/index.html`
  - [ ] File upload form
  - [ ] Job description text area
  - [ ] Submit button
  - [ ] Results display area
- [ ] 5.2 Add basic CSS styling
- [ ] 5.3 JavaScript to call API and show results

---

## Phase 6: Database Integration
**Goal:** Save analysis history to PostgreSQL

### Tasks:
- [ ] 6.1 Set up PostgreSQL locally (or use Docker)
- [ ] 6.2 Create database tables
- [ ] 6.3 Save each analysis to database
- [ ] 6.4 Retrieve history for users

---

## Phase 7: Deployment
**Goal:** Put it online so others can use it

### Tasks:
- [ ] 7.1 Choose platform (Railway, Render, Heroku, etc.)
- [ ] 7.2 Set up environment variables
- [ ] 7.3 Deploy backend
- [ ] 7.4 Deploy database
- [ ] 7.5 Test live version

---

## Current Status
**You are here:** Phase 1 - File Parsing

**What you've done:**
- ✅ Project structure created
- ✅ Git repo set up
- ✅ Architecture diagram done
- ✅ OpenAI API working
- ✅ Requirements installed

**Next immediate task:** Create the file parser service (1.1)