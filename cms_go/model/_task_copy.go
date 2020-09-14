package model

import (
	"time"
)

type Participation struct {
	ID int64
}

type Task struct {
	ID int64
}

type File struct {
	ID         int64
	Submission *Submission
	Filename   string
	Digest     string
}

type SubmissionResult struct {
	ID int64
}

type Token struct {
	ID int64
}

type Submission struct {
	ID            int64
	Participation *Participation
	Task          *Task
	Timestamp     *time.Time `gorm:"not null"`
	Language      string
	Comment       string `gorm:"default:'';not null"`
	Official      bool   `gorm:"default:false;not null"`
	Files         []*File
	Token         []*Token
	Results       []*SubmissionResult
}

type Dataset struct {
	ID int64
}

type Statement struct {
	ID   int64
	Task *Task
}
