# JobFit Architecture

## System Overview
```mermaid

## Data Flow

1. User uploads CV + Job Description
2. FastAPI receives files
3. File Service extracts text from PDF/DOCX
4. AI Service sends to Claude for analysis
5. Results stored in PostgreSQL
6. Response sent back to user


https://supabase.com/!!
--Ernesto314!!