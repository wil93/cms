package main

import (
	"context"
	"fmt"
	"time"

	pgx "github.com/jackc/pgx/v4"

	model "github.com/cms-dev/cms/v2/model"
)

func main() {
	conn, err := pgx.Connect(
		context.Background(),
		"postgresql://localhost:5432/testdb",
	)
	defer conn.Close(context.Background())

	// Select all users.
	var users []model.User
	err := db.Model(&users).Select()
	if err != nil {
		panic(err)
	}

	fmt.Println(users)
	fmt.Println("cmsScoringService...")
	fmt.Println(model.ReverseRunes("cmsScoringService..."))

	fmt.Println("The time is", time.Now())
}
