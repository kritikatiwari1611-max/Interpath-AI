# InternPath AI - Final Year Project Report Outline

## Chapter 1: Introduction
- 1.1 Problem Statement: Career navigation and skill gap uncertainty among undergraduate students (BCA, B.Tech, B.Com, BBA).
- 1.2 Motivation: Lack of explainable, actionable roadmaps on generic job portals.
- 1.3 Project Objectives: 13 core functional goals mapping to system capabilities.
- 1.4 Scope and Limitations: Offline-first architecture, deterministic scoring, demonstrative opportunities.

## Chapter 2: Literature Survey & Background Study
- 2.1 Survey of Existing Career Portals (LinkedIn, Indeed, Internshala).
- 2.2 Comparative Analysis: AI Generative Advising vs. Deterministic Rule-Based Assessment.
- 2.3 Need for Transparent, Multi-Disciplinary Career Roadmaps for Technical and Non-Technical Disciplines.

## Chapter 3: System Requirements & Architecture
- 3.1 Functional Requirements (Authentication, Profile, Gap Analysis, 4-Stage Roadmap, Learning Hub, Mock Interview, Readiness Engine).
- 3.2 Non-Functional Requirements (Security, Performance, Offline PWA Shell, Accessibility).
- 3.3 System Architecture Diagram & Data Flow.
- 3.4 Technology Stack Justification (Python Flask, Vanilla HTML5/CSS3/JS, SQLite / PostgreSQL).

## Chapter 4: Database Design & Knowledge Base
- 4.1 Relational Schema Design (users, student_profiles, user_skills, user_projects, roadmap_tasks, interview_attempts, readiness_snapshots).
- 4.2 Database Indexing Strategy.
- 4.3 Knowledge Base JSON Specifications (roles.json, weights.json, interview_questions.json, resources.json, internships_demo.json).

## Chapter 5: Algorithm & Engine Implementation
- 5.1 Deterministic Skill-Gap Analysis Algorithm.
- 5.2 Dynamic 4-Stage Roadmap Generation Logic.
- 5.3 Transparent Internship Readiness Scoring Engine (Weighted Multipliers and Role Overrides).
- 5.4 Hybrid AI Engine & Fallback Demo Provider.
- 5.5 Keyword & Rule-Based Interview Evaluation.

## Chapter 6: User Interface & Frontend Implementation
- 6.1 Design System: Responsive Layout, Navy Sidebar, Royal Blue Accents.
- 6.2 Accessible Top Navigation & Three-Dot (⋮) Menu Component.
- 6.3 PWA Service Worker Implementation & Offline FIFO Outbox Architecture.

## Chapter 7: Testing & Verification
- 7.1 Test Strategy & Automated Unit Test Suite (pytest).
- 7.2 Validation of Deterministic Edge Cases (Empty profiles, Non-technical separation, Irrelevant projects).
- 7.3 Security Testing (Rate limiting, CSRF tokens, Account deletion).
- 7.4 Verification Scenarios (a)-(f) Execution Results.

## Chapter 8: Conclusion & Future Enhancements
- 8.1 Summary of Contributions.
- 8.2 Future Scope: Machine Learning Collaborative Filtering, Resume PDF Parsing with NLP, Live Job Board API Integration.
