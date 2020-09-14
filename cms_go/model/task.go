package model

type Task struct {
	ID                int64
	Num               int32
	Contest           *Contest
	Name              string `gorm:"unique;not null"`
	Title             string `gorm:"not null"`
	SubmissionFormat  string
	PrimaryStatements []string
}

type Statement struct {
	ID   int64
	Task *Task
}
