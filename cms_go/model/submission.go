package model

import (
	"time"
)

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

func ReverseRunes(s string) string {
	r := []rune(s)
	for i, j := 0, len(r)-1; i < len(r)/2; i, j = i+1, j-1 {
		r[i], r[j] = r[j], r[i]
	}
	return string(r)
}
