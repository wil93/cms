package main

import (
	"embed"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"regexp"
	"strconv"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type User struct {
	ID                 int64
	FirstName          string `gorm:"not null"`
	LastName           string `gorm:"not null"`
	Username           string `gorm:"unique;not null"`
	Password           string `gorm:"not null"`
	Email              string
	Timezone           string
	// PreferredLanguages []string
	// Participations     []*Participation
}

type Contest struct {
    ID int64
    Name string
    Description string
}

type config struct {
    Database string
}

type TemplateData struct {
    Title string
}

func main() {
    contestIDFlag := flag.String("c", "ALL", "the numeric contest ID or the 'ALL' string")
    flag.Parse()

    // TODO: parse the JSON file located at: /usr/local/etc/cms.conf
    pythonConfigJSONString := `{"database": "postgresql+psycopg2://williamdiluigi:your_password_here@localhost:5432/testdb"}`

    var pythonConfig config
    json.Unmarshal([]byte(pythonConfigJSONString), &pythonConfig)

    re := regexp.MustCompile(":\\/\\/(.+):(.+)@(.+):(.*)\\/(.*)$")
    match := re.FindStringSubmatch(pythonConfig.Database)

    // dsn := fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%s sslmode=disable TimeZone=Europe/Zurich", match[3], match[1], match[2], match[5], match[4])
    dsn := fmt.Sprintf("host=%s user=%s dbname=%s port=%s sslmode=disable TimeZone=Europe/Zurich", match[3], match[1], match[5], match[4])
    db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})

    if err != nil {
        fmt.Println("Failed when connecting to the database.")
        return
    }

    var contest Contest

    var contestID int64
    if *contestIDFlag != "ALL" {
        contestID, err = strconv.ParseInt(*contestIDFlag, 10, 64)

        fmt.Println(fmt.Sprint(contestID))

        if err != nil {
            panic("The contest ID provided is not valid")
        }
    }

    db.First(&contest, contestID);

    http.HandleFunc("/", func (w http.ResponseWriter, r *http.Request) {
        w.Write([]byte(contest.Description))
    })

    //go:embed static/*
    var static embed.FS

    http.Handle("/static/", http.FileServer(http.FS(static)))

    http.ListenAndServe(":8888", nil)
}
