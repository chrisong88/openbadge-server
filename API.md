#OpenBadge API -- The working bits

##Overview
The basic idea in this backend is that there should be only one way to do anything. 
This sometimes means requiring two or more API calls for something that ought to take
one, but it is my belief that this makes it simpler. The exception to this is in first creation
of a project, where one may supply the hubs and badges to initialize, skipping over 
the `PUT /:projectID/hubs` and `PUT /:projectID/badges` endpoints.

All standard connections will start with a `GET` to `/projects`, and henceforth 
use the `projectID` returned by that request to communicate with the server, in the form of
`PUT`'s, `GET`'s, and `POST`'s to `/:projectID/[meetings, hubs, badges]`

There exist a collection of `God` level endpoints. These require a special key that will
not be available to any hubs meant for use by the end user. All other endpoints are restricted
to hubs that are members of the project being accessed. 

In general Headers are used exclusively for Authentication, either via a `X-GODKEY` for God-level
endpoints, or by the `badgeID` (ng-Device's `uuid`). The exeption to this is in `GET`'s, which 
sometimes use headers to specify what is to be gotten.






##Endpoints
####Project Level Endpoints
Method                |        Path            | Summary                       | Accessible To
----------------------|------------------------|-------------------------------|------------------------------
[GET](#getproject)    | /projects              | get project's badges/members  | Project's Hubs

####Meeting Level Endpoints
Method                |        Path            | Summary                       | Accessible To
----------------------|------------------------|-------------------------------|------------------------------
[PUT](#putmeeting)    | /:projectID/meetings   | initialize a meeting          | Project's Hubs
[GET](#getmeeting)    | /:projectID/meetings   | get the meetings for a project| Project's Hubs
[POST](#postmeeting)  | /:projectID/meetings   | add data to a meeting        | Project's Hubs


####Hub Level Endpoints
Method                |        Path            | Summary                       | Accessible To
----------------------|------------------------|-------------------------------|------------------------------
[PUT](#puthub)        | /:anyNumber/hubs       | add hub to defualt project    | All    
[GET](#gethub)        | /:projectID/hubs       | get hub's metadata and projects| Project's Hubs











##Project Level Endpoints

<a name="getproject"></a>
###GET /projects

Get badge ownership info and `project_id` for a hub

**Headers Passed**

Key          | Type    |
-------------|---------|
X-HUB-UUID   | text    |

*Response Codes*
- 200 - got project info
- 404 - hubID not found?

**Returned JSON**

```json
{
  "project": {
    "active_meetings": [],
    "key": "OROMVGQFGH",
    "badge_map": {
      "FA:DF:C3:8C:99:3C": {
        "name": "Eleni Andrikos",
        "key": "BLWQE3O527"
      },
      "F2:74:78:84:E2:76": {
        "name": "Walaa Al",
        "key": "61JQH99IMA"
      },
      "FB:29:43:AC:9B:70": {
        "name": "Oren Lederman",
        "key": "1WREPE6TJ2"
      },
      "D2:3C:F6:B9:87:24": {
        "name": "Gestina Yassa",
        "key": "Q0Y5VSMRJR"
      },
      "EF:18:8D:7E:4C:F3": {
        "name": "Jackson Kearl",
        "key": "9M4XMOUV96"
      }
    },
    "members": {
      "Jackson Kearl": {
        "badge": "EF:18:8D:7E:4C:F3",
        "id": 12,
        "name": "Jackson Kearl"
      },
      "Eleni Andrikos": {
        "badge": "FA:DF:C3:8C:99:3C",
        "id": 13,
        "name": "Eleni Andrikos"
      },
      "Walaa Al": {
        "badge": "F2:74:78:84:E2:76",
        "id": 15,
        "name": "Walaa Al"
      },
      "Oren Lederman": {
        "badge": "FB:29:43:AC:9B:70",
        "id": 11,
        "name": "Oren Lederman"
      },
      "Gestina Yassa": {
        "badge": "D2:3C:F6:B9:87:24",
        "id": 14,
        "name": "Gestina Yassa"
      }
    },
    "id": 4,
    "name": "Test Project 1"
  },
  "hub": {
    "last_updates": {
      "Proj1| 1470997887.655": 6
    },
    "name": "My Computer",
    "su": true
  }
}
```




















##Meeting Level Endpoints


<a name="putmeeting"></a>
###PUT /:projectID/meetings

Create a meeting with given logfile.

**Headers Passed**

Key          | Type    |
-------------|---------|
X-HUB-UUID   | text    |


**Body**

```json
meeting_init_data:{"type":"meeting started","log_index":0,"log_timestamp": 1470997887.655,"data":{"log_version":"2.1","uuid":"Proj1| 1470997887.655"}}
```

*Response Codes*
- 200 - meeting created
- 401 - hub doesn't belong to project
- 404 - hubUUID not found

**Returned JSON**

```json
{
  "details": "meeting created"
}
```




<a name="getmeeting"></a>
###GET /:projectID/meetings

Get all meetigns in a project, with or without thier respective files. 

If X-GET-FILES.lower() is equal to "true", this will return a UUID-accessible Associated Array of metadata and chunk
as separate entries in a dictionary. Otherwise, it will return a UUID-accessible Associated Array of metadata objects

**Headers Passed**

Key          | Type    |
-------------|---------|
X-HUB-UUID   | text    |
X-GET-FILES  | text    |


*Response Codes*
- 200 - got meetings
- 401 - hub doesn't belong to project
- 404 - hubUUID not found

**Returned JSON**

```json
{
  "meetings": {
    "Proj1| 1470997888.655": {
      "events": [
        {
          "data": {
            "uuid": "Proj1| 1470997888.655",
            "log_version": "2.1",
            "start_time": 1470997887.655,
            "is_active": true,
            "members": {},
            "hubs": {}
          },
          "log_timestamp": "1470997887.655",
          "type": "meeting started",
          "hub": "Proj1Comp1",
          "log_index": 0
        }
      ],
      "metadata": {
        "uuid": "Proj1| 1470997888.655",
        "log_version": "2.1",
        "start_time": 1470997887.655,
        "is_active": true,
        "members": {},
        "hubs": {}
      }
    },
    "Proj1| 1470997887.655": {
      "events": [
        {
          "data": {
            "key": "1WREPE6TJ2"
          },
          "log_timestamp": "1470637514.450",
          "type": "member joined",
          "hub": "Proj1Comp1",
          "log_index": 2
        },
        {
          "data": {
            "key": "9M4XMOUV96"
          },
          "log_timestamp": "1470637514.451",
          "type": "member joined",
          "hub": "Proj1Comp1",
          "log_index": 3
        },
        {
          "data": {
            "locale": "GMT-0400 (EDT)"
          },
          "log_timestamp": "1470637960.240",
          "type": "hub joined",
          "hub": "Proj1Comp1",
          "log_index": 1
        },
        {
          "data": {
            "uuid": "Proj1| 1470997887.655",
            "log_version": "2.1",
            "start_time": 1470997887.655,
            "is_active": false,
            "end_time": 1470999890,
            "members": {
              "1WREPE6TJ2": {
                "active": false,
                "timestamp": 1470997990.655
              },
              "9M4XMOUV96": {
                "active": false,
                "timestamp": 1470997990.655
              },
              "1WREPE6TJ": {
                "active": true,
                "timestamp": 1470637514.45
              }
            },
            "hubs": {
              "Proj1Comp1": {
                "active": true,
                "timestamp": 1470637960.24
              }
            }
          },
          "log_timestamp": "1470997887.655",
          "type": "meeting started",
          "hub": "Proj1Comp1",
          "log_index": 0
        },
        {
          "data": {
            "key": "1WREPE6TJ2"
          },
          "log_timestamp": "1470997990.655",
          "type": "member left",
          "hub": "Proj1Comp1",
          "log_index": 4
        },
        {
          "data": {
            "key": "9M4XMOUV96"
          },
          "log_timestamp": "1470997990.655",
          "type": "member left",
          "hub": "Proj1Comp1",
          "log_index": 5
        },
        {
          "data": {
            "method": "manual"
          },
          "log_timestamp": "1470999890.000",
          "type": "meeting ended",
          "hub": "Proj1Comp1",
          "log_index": 6
        }
      ],
      "metadata": {
        "uuid": "Proj1| 1470997887.655",
        "log_version": "2.1",
        "start_time": 1470997887.655,
        "is_active": false,
        "end_time": 1470999890,
        "members": {
          "1WREPE6TJ2": {
            "active": false,
            "timestamp": 1470997990.655
          },
          "9M4XMOUV96": {
            "active": false,
            "timestamp": 1470997990.655
          },
          "1WREPE6TJ": {
            "active": true,
            "timestamp": 1470637514.45
          }
        },
        "hubs": {
          "Proj1Comp1": {
            "active": true,
            "timestamp": 1470637960.24
          }
        }
      }
    }
  }
}
```








<a name="postmeeting"></a>
###POST /:projectID/meetings

Add chunks to a meeting

**Headers Passed**

Key          | Type    |
-------------|---------|
X-HUB-UUID  | text    |
X-MEETING-UUID| text|

**Passed JSON**
```json
["{"uuid":"12345","start_time":"2016-07-02T15:31:07.767Z","location":"meetingroom","type":"study","description":""}", ...
//chunk data as JSON'd list of JSON'd objects
]
```

*Response Codes*
- 200 - chunks added


**Returned JSON**

```json
{
  "details": "data added"
}
```


















##Hub Level Endpoints

<a name="puthub"></a>
###PUT /:anyNumber/hubs

Create a hub in the default project.

**Headers Passed**

Key          | Type    |
-------------|---------|
X-APP-UUID   | text    |
X-PROJECT-NAME |text|

*Response Codes*
- 200 - hub created
- 400 - bad request (no UUID?)
- 500 - bad UUID, already registered?


**Returned JSON**

```json
{
  "status": "added to project",
  "project": {
    "active_meetings": [
      {
        "uuid": "Proj1| 1470997888.655",
        "log_version": "2.1",
        "start_time": 1470997887.655,
        "is_active": true,
        "members": {},
        "hubs": {}
      }
    ],
    "key": "OROMVGQFGH",
    "badge_map": {
      "FA:DF:C3:8C:99:3C": {
        "name": "Eleni Andrikos",
        "key": "BLWQE3O527"
      },
      "F2:74:78:84:E2:76": {
        "name": "Walaa Al",
        "key": "61JQH99IMA"
      },
      "FB:29:43:AC:9B:70": {
        "name": "Oren Lederman",
        "key": "1WREPE6TJ2"
      },
      "D2:3C:F6:B9:87:24": {
        "name": "Gestina Yassa",
        "key": "Q0Y5VSMRJR"
      },
      "EF:18:8D:7E:4C:F3": {
        "name": "Jackson Kearl",
        "key": "9M4XMOUV96"
      }
    },
    "members": {
      "Jackson Kearl": {
        "badge": "EF:18:8D:7E:4C:F3",
        "id": 12,
        "name": "Jackson Kearl"
      },
      "Eleni Andrikos": {
        "badge": "FA:DF:C3:8C:99:3C",
        "id": 13,
        "name": "Eleni Andrikos"
      },
      "Walaa Al": {
        "badge": "F2:74:78:84:E2:76",
        "id": 15,
        "name": "Walaa Al"
      },
      "Oren Lederman": {
        "badge": "FB:29:43:AC:9B:70",
        "id": 11,
        "name": "Oren Lederman"
      },
      "Gestina Yassa": {
        "badge": "D2:3C:F6:B9:87:24",
        "id": 14,
        "name": "Gestina Yassa"
      }
    },
    "id": 4,
    "name": "Test Project 1"
  },
  "hub": {
    "last_updates": {
      "Proj1| 1470997887.655": 6
    },
    "name": "My Computer",
    "su": true
  }
}
```


<a name="gethub"></a>
###GET /:projectID/hubs

Get hub's name and meetings, with all members added since given timestamp

**Headers Passed**

Key          | Type    |
-------------|---------|
X-HUB-UUID   | text    |
X-LAST-UPDATE


*Response Codes*
- 200 - got hub data
- 401 - hub doesn't belong to project
- 404 - hubUUID not found

**Returned JSON**

```json
{
  "badge_map": {
    "FA:DF:C3:8C:99:3C": {
      "name": "Eleni Andrikos",
      "key": "BLWQE3O527"
    },
    "F2:74:78:84:E2:76": {
      "name": "Walaa Al",
      "key": "61JQH99IMA"
    },
    "FB:29:43:AC:9B:70": {
      "name": "Oren Lederman",
      "key": "1WREPE6TJ2"
    },
    "D2:3C:F6:B9:87:24": {
      "name": "Gestina Yassa",
      "key": "Q0Y5VSMRJR"
    },
    "EF:18:8D:7E:4C:F3": {
      "name": "Jackson Kearl",
      "key": "9M4XMOUV96"
    }
  },
  "meeting": {
    "uuid": "Proj1| 1470997888.655",
    "log_version": "2.1",
    "start_time": 1470997887.655,
    "is_active": true,
    "members": {},
    "hubs": {}
  },
  "su": true,
  "last_update": 0
}
```

















































##Documentation Format
####(courtesy of [Conner DiPaolo](https://github.com/cdipaolo))

Keep documentation in this format please!

Add the method to the [path overview](#paths) and place it under the correct [section](#sections)

```markdown
<a name="briefname"></a>
###METHOD /path/to/endpoint

put a decent description of what the endpoint does here

**Headers Passed**

Key   | Type    | Description
------|---------|------------
key   | string  | here's a header description

**Passed JSON**
{
  "example":"of",
  "passed":"json",
  "goes":{
    "here":true
  }
}


*Response Codes*
- 400 - invalid request
- 200 - OK
- 201 - thing was created
- 401 - unauthorized

**Returned JSON**
{
  "example":"of",
  "return":"json",
  "goes":{
    "here":true
  }
}

#####Comments

put notes here about, for example, optional parameters and/or specific types

```