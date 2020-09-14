package model

import "time"

type User struct {
	ID                 int64
	FirstName          string `gorm:"not null"`
	LastName           string `gorm:"not null"`
	Username           string `gorm:"unique;not null"`
	Password           string `gorm:"not null"`
	Email              string
	Timezone           string
	PreferredLanguages []string
	// Participations     []*Participation
}

type Team struct {
	ID             int64
	Code           string `gorm:"unique;not null"`
	Name           string `gorm:"not null"`
	Participations []*Participation
}

type Participation struct {
	ID           int64
	StartingTime *time.Time
	DelayTime    *time.Time
	ExtraTime    *time.Time
	Password     string
	Hidden       bool `gorm:"default:false;not null"`
	Unrestricted bool `gorm:"default:false;not null"`
	Contest      *Contest
	User         *User
	Team         *Team
	Submissions  []*Submission
	// UserTests    []*UserTest
	// Messages     []*Message
	// Questions    []*Question
	// PrintJobs    []*PrintJob
}
