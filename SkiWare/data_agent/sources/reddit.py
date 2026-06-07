import logging
import os

import praw

from data_agent.sources.base import Document, Source

logger = logging.getLogger(__name__)

MIN_POST_SCORE = 10
MIN_TEXT_LENGTH = 100
MIN_COMMENT_SCORE = 3
MIN_COMMENT_LENGTH = 50

SUBREDDITS = ["skiing", "snowboarding"]

BRAND_QUERIES = [
    # Alpine ski brands
    "rossignol repair OR damage OR base OR tune OR wax",
    "k2 skis repair OR damage OR base OR tune OR wax",
    "atomic skis repair OR damage OR base OR tune OR wax",
    "salomon skis repair OR damage OR base OR tune OR wax",
    "volkl repair OR damage OR base OR tune OR wax",
    "head skis repair OR damage OR base OR tune OR wax",
    "blizzard skis repair OR damage OR base OR tune OR wax",
    "line skis repair OR damage OR base OR tune OR wax",
    "faction skis repair OR damage OR base OR tune OR wax",
    "fischer skis repair OR damage OR base OR tune OR wax",
    "dynastar repair OR damage OR base OR tune OR wax",
    "nordica skis repair OR damage OR base OR tune OR wax",
    "elan skis repair OR damage OR base OR tune OR wax",
    "black crows skis repair OR damage OR base OR tune OR wax",
    "armada skis repair OR damage OR base OR tune OR wax",
    "DPS skis repair OR damage OR base OR tune OR wax",
    "moment skis repair OR damage OR base OR tune OR wax",
    "icelantic repair OR damage OR base OR tune OR wax",
    "liberty skis repair OR damage OR base OR tune OR wax",
    "ON3P skis repair OR damage OR base OR tune OR wax",
    "4FRNT skis repair OR damage OR base OR tune OR wax",
    "kastle skis repair OR damage OR base OR tune OR wax",
    "stockli skis repair OR damage OR base OR tune OR wax",
    "weston skis repair OR damage OR base OR tune OR wax",
    "scott skis repair OR damage OR base OR tune OR wax",
    "j skis repair OR damage OR base OR tune OR wax",
    "zag skis repair OR damage OR base OR tune OR wax",
    # Snowboard brands
    "burton snowboard repair OR damage OR base OR tune OR wax",
    "capita snowboard repair OR damage OR base OR tune OR wax",
    "jones snowboard repair OR damage OR base OR tune OR wax",
    "gnu snowboard repair OR damage OR base OR tune OR wax",
    "never summer snowboard repair OR damage OR base OR tune OR wax",
    "lib tech snowboard repair OR damage OR base OR tune OR wax",
    "arbor snowboard repair OR damage OR base OR tune OR wax",
    "bataleon snowboard repair OR damage OR base OR tune OR wax",
    "ride snowboard repair OR damage OR base OR tune OR wax",
    "rome snowboard repair OR damage OR base OR tune OR wax",
    "nitro snowboard repair OR damage OR base OR tune OR wax",
    "yes snowboard repair OR damage OR base OR tune OR wax",
    "endeavor snowboard repair OR damage OR base OR tune OR wax",
    "prior snowboard repair OR damage OR base OR tune OR wax",
]

MODEL_QUERIES = [
    # Rossignol
    '"rossignol experience" repair OR damage OR tune',
    '"rossignol experience 76" repair OR damage OR tune',
    '"rossignol experience 82" repair OR damage OR tune',
    '"rossignol experience 86" repair OR damage OR tune',
    '"rossignol experience 88" repair OR damage OR tune',
    '"rossignol experience 92" repair OR damage OR tune',
    '"rossignol experience 98" repair OR damage OR tune',
    '"rossignol blackops" repair OR damage OR tune',
    '"rossignol black ops sender" repair OR damage OR tune',
    '"rossignol black ops escaper" repair OR damage OR tune',
    '"rossignol black ops blazer" repair OR damage OR tune',
    '"rossignol soul 7" repair OR damage OR tune',
    '"rossignol rallybird" repair OR damage OR tune',
    '"rossignol hero" repair OR damage OR tune',
    # K2
    '"k2 mindbender" repair OR damage OR tune',
    '"k2 mindbender 90" repair OR damage OR tune',
    '"k2 mindbender 96" repair OR damage OR tune',
    '"k2 mindbender 99" repair OR damage OR tune',
    '"k2 mindbender 106" repair OR damage OR tune',
    '"k2 mindbender 108" repair OR damage OR tune',
    '"k2 disruption" repair OR damage OR tune',
    '"k2 wayback" repair OR damage OR tune',
    '"k2 reckoner" repair OR damage OR tune',
    '"k2 poacher" repair OR damage OR tune',
    '"k2 pinnacle" repair OR damage OR tune',
    # Atomic
    '"atomic bent chetler" repair OR damage OR tune',
    '"bent chetler 90" repair OR damage OR tune',
    '"bent chetler 100" repair OR damage OR tune',
    '"bent chetler 120" repair OR damage OR tune',
    '"bent chetler mini" repair OR damage OR tune',
    '"atomic vantage" repair OR damage OR tune',
    '"atomic redster" repair OR damage OR tune',
    '"atomic maverick" repair OR damage OR tune',
    '"atomic backland" repair OR damage OR tune',
    # Salomon
    '"salomon qst" repair OR damage OR tune',
    '"salomon qst 85" repair OR damage OR tune',
    '"salomon qst 92" repair OR damage OR tune',
    '"salomon qst 98" repair OR damage OR tune',
    '"salomon qst 106" repair OR damage OR tune',
    '"salomon stance" repair OR damage OR tune',
    '"salomon stance 84" repair OR damage OR tune',
    '"salomon stance 88" repair OR damage OR tune',
    '"salomon stance 94" repair OR damage OR tune',
    '"salomon stance 96" repair OR damage OR tune',
    # Volkl
    '"volkl mantra" repair OR damage OR tune',
    '"volkl kendo" repair OR damage OR tune',
    '"volkl revolt" repair OR damage OR tune',
    '"volkl blaze" repair OR damage OR tune',
    '"volkl deacon" repair OR damage OR tune',
    '"volkl katana" repair OR damage OR tune',
    # Head
    '"head kore" repair OR damage OR tune',
    '"head kore 87" repair OR damage OR tune',
    '"head kore 93" repair OR damage OR tune',
    '"head kore 97" repair OR damage OR tune',
    '"head kore 99" repair OR damage OR tune',
    '"head kore 105" repair OR damage OR tune',
    '"head kore 111" repair OR damage OR tune',
    '"head monster" repair OR damage OR tune',
    '"head reverb" repair OR damage OR tune',
    # Blizzard
    '"blizzard brahma" repair OR damage OR tune',
    '"blizzard rustler" repair OR damage OR tune',
    '"blizzard rustler 9" repair OR damage OR tune',
    '"blizzard rustler 10" repair OR damage OR tune',
    '"blizzard rustler 11" repair OR damage OR tune',
    '"blizzard bonafide" repair OR damage OR tune',
    '"blizzard zero g" repair OR damage OR tune',
    '"blizzard black pearl" repair OR damage OR tune',
    '"blizzard sheeva" repair OR damage OR tune',
    '"blizzard hustle" repair OR damage OR tune',
    # Line
    '"line blade optic" repair OR damage OR tune',
    '"line sick day" repair OR damage OR tune',
    '"line sick day 89" repair OR damage OR tune',
    '"line sick day 94" repair OR damage OR tune',
    '"line sick day 104" repair OR damage OR tune',
    '"line vision" repair OR damage OR tune',
    '"line honey badger" repair OR damage OR tune',
    '"line sir francis bacon" repair OR damage OR tune',
    '"line pescado" repair OR damage OR tune',
    '"line chronic" repair OR damage OR tune',
    # Faction
    '"faction prodigy" repair OR damage OR tune',
    '"faction candide" repair OR damage OR tune',
    '"faction agent" repair OR damage OR tune',
    '"faction mana" repair OR damage OR tune',
    # Fischer
    '"fischer ranger" repair OR damage OR tune',
    '"fischer ranger 84" repair OR damage OR tune',
    '"fischer ranger 90" repair OR damage OR tune',
    '"fischer ranger 102" repair OR damage OR tune',
    '"fischer ranger 108" repair OR damage OR tune',
    '"fischer transalp" repair OR damage OR tune',
    # Dynastar
    '"dynastar m-cross" repair OR damage OR tune',
    '"dynastar speed" repair OR damage OR tune',
    '"dynastar m-free" repair OR damage OR tune',
    # Nordica
    '"nordica enforcer" repair OR damage OR tune',
    '"nordica enforcer 88" repair OR damage OR tune',
    '"nordica enforcer 93" repair OR damage OR tune',
    '"nordica enforcer 100" repair OR damage OR tune',
    '"nordica enforcer 110" repair OR damage OR tune',
    '"nordica santa ana" repair OR damage OR tune',
    '"nordica santa ana 88" repair OR damage OR tune',
    '"nordica santa ana 98" repair OR damage OR tune',
    '"nordica spitfire" repair OR damage OR tune',
    '"nordica dobermann" repair OR damage OR tune',
    # Elan
    '"elan ripstick" repair OR damage OR tune',
    '"elan ripstick 86" repair OR damage OR tune',
    '"elan ripstick 94" repair OR damage OR tune',
    '"elan ripstick 102" repair OR damage OR tune',
    '"elan wingman" repair OR damage OR tune',
    '"elan amphibio" repair OR damage OR tune',
    # Black Crows
    '"black crows orb" repair OR damage OR tune',
    '"black crows corvus" repair OR damage OR tune',
    '"black crows camox" repair OR damage OR tune',
    '"black crows navis" repair OR damage OR tune',
    '"black crows daemon" repair OR damage OR tune',
    '"black crows atris" repair OR damage OR tune',
    # Armada
    '"armada arv" repair OR damage OR tune',
    '"armada arv 84" repair OR damage OR tune',
    '"armada arv 96" repair OR damage OR tune',
    '"armada arv 106" repair OR damage OR tune',
    '"armada tracer" repair OR damage OR tune',
    '"armada declivity" repair OR damage OR tune',
    '"armada locator" repair OR damage OR tune',
    # DPS
    '"dps pagoda" repair OR damage OR tune',
    '"dps wailer" repair OR damage OR tune',
    '"dps lotus" repair OR damage OR tune',
    # Moment
    '"moment deathwish" repair OR damage OR tune',
    '"moment governor" repair OR damage OR tune',
    '"moment bibby" repair OR damage OR tune',
    '"moment wildcat" repair OR damage OR tune',
    # Icelantic
    '"icelantic nomad" repair OR damage OR tune',
    '"icelantic shaman" repair OR damage OR tune',
    '"icelantic sabre" repair OR damage OR tune',
    '"icelantic oracle" repair OR damage OR tune',
    # Liberty
    '"liberty origin" repair OR damage OR tune',
    '"liberty genesis" repair OR damage OR tune',
    '"liberty helix" repair OR damage OR tune',
    # ON3P
    '"on3p woodsman" repair OR damage OR tune',
    '"on3p kartel" repair OR damage OR tune',
    # Weston
    '"weston backwoods" repair OR damage OR tune',
    '"weston verve" repair OR damage OR tune',
    # Scott
    '"scott scrapper" repair OR damage OR tune',
    '"scott superguide" repair OR damage OR tune',
    # Burton
    '"burton custom" repair OR damage OR tune',
    '"burton custom flying v" repair OR damage OR tune',
    '"burton process" repair OR damage OR tune',
    '"burton deep thinker" repair OR damage OR tune',
    '"burton skeleton key" repair OR damage OR tune',
    '"burton instigator" repair OR damage OR tune',
    '"burton ripcord" repair OR damage OR tune',
    '"burton family tree" repair OR damage OR tune',
    '"burton genesis" repair OR damage OR tune',
    '"burton feather" repair OR damage OR tune',
    # Capita
    '"capita doa" repair OR damage OR tune',
    '"capita defenders of awesome" repair OR damage OR tune',
    '"capita mercury" repair OR damage OR tune',
    '"capita ultrafear" repair OR damage OR tune',
    '"capita pathfinder" repair OR damage OR tune',
    # Jones
    '"jones mountain twin" repair OR damage OR tune',
    '"jones flagship" repair OR damage OR tune',
    '"jones explorer" repair OR damage OR tune',
    '"jones stratos" repair OR damage OR tune',
    '"jones dream catcher" repair OR damage OR tune',
    # GNU
    '"gnu riders choice" repair OR damage OR tune',
    '"gnu money" repair OR damage OR tune',
    '"gnu antigravity" repair OR damage OR tune',
    '"gnu ladies choice" repair OR damage OR tune',
    # Never Summer
    '"never summer proto type two" repair OR damage OR tune',
    '"never summer shaper twin" repair OR damage OR tune',
    '"never summer ripsaw" repair OR damage OR tune',
    '"never summer harpoon" repair OR damage OR tune',
    '"never summer snowtrooper" repair OR damage OR tune',
    # Lib Tech
    '"lib tech t.rice" repair OR damage OR tune',
    '"lib tech travis rice" repair OR damage OR tune',
    '"lib tech box knife" repair OR damage OR tune',
    '"lib tech cold brew" repair OR damage OR tune',
    '"lib tech skunk ape" repair OR damage OR tune',
    '"lib tech stump ape" repair OR damage OR tune',
    # Arbor
    '"arbor wasteland" repair OR damage OR tune',
    '"arbor formula" repair OR damage OR tune',
    '"arbor draft" repair OR damage OR tune',
    '"arbor foundation" repair OR damage OR tune',
    # Bataleon
    '"bataleon party wave" repair OR damage OR tune',
    '"bataleon evil twin" repair OR damage OR tune',
    '"bataleon disaster" repair OR damage OR tune',
    '"bataleon global warmer" repair OR damage OR tune',
    # Ride
    '"ride warpig" repair OR damage OR tune',
    '"ride helix" repair OR damage OR tune',
    '"ride crankcase" repair OR damage OR tune',
    '"ride twinpig" repair OR damage OR tune',
    # Rome
    '"rome mechanic" repair OR damage OR tune',
    '"rome agent" repair OR damage OR tune',
    '"rome reverb" repair OR damage OR tune',
    # Nitro
    '"nitro beast" repair OR damage OR tune',
    '"nitro team" repair OR damage OR tune',
    '"nitro mystique" repair OR damage OR tune',
    # Yes
    '"yes basic" repair OR damage OR tune',
    '"yes typo" repair OR damage OR tune',
    '"yes optimistic" repair OR damage OR tune',
]


def _comment_limit(post_score: int) -> int:
    if post_score >= 500:
        return 15
    if post_score >= 100:
        return 10
    return 5


class RedditSource(Source):
    def fetch(self) -> list[Document]:
        client_id = os.environ.get("REDDIT_CLIENT_ID")
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET")

        if not client_id or not client_secret:
            missing = [
                v for v, val in [
                    ("REDDIT_CLIENT_ID", client_id),
                    ("REDDIT_CLIENT_SECRET", client_secret),
                ]
                if not val
            ]
            logger.warning(
                f"Missing Reddit credentials: {', '.join(missing)} — skipping RedditSource"
            )
            return []

        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="skiware-data-agent/1.0",
        )

        docs: list[Document] = []
        seen_post_ids: set[str] = set()
        seen_comment_ids: set[str] = set()

        for subreddit_name in SUBREDDITS:
            subreddit = reddit.subreddit(subreddit_name)
            for query in BRAND_QUERIES + MODEL_QUERIES:
                try:
                    for post in subreddit.search(query, sort="relevance", limit=10):
                        if post.id in seen_post_ids:
                            continue
                        if post.score < MIN_POST_SCORE:
                            continue
                        if len(post.selftext) < MIN_TEXT_LENGTH:
                            continue

                        seen_post_ids.add(post.id)
                        docs.append(
                            Document(
                                url=post.url,
                                title=post.title,
                                content=post.selftext,
                                source_type="reddit",
                                metadata={
                                    "upvotes": post.score,
                                    "reply_count": post.num_comments,
                                    "subreddit": subreddit_name,
                                    "post_id": post.id,
                                },
                            )
                        )

                        # Fetch top comments
                        limit = _comment_limit(post.score)
                        try:
                            post.comments.replace_more(limit=0)
                            count = 0
                            top_comments = sorted(
                                post.comments.list(),
                                key=lambda c: getattr(c, "score", 0),
                                reverse=True,
                            )
                            for comment in top_comments:
                                if count >= limit:
                                    break
                                if comment.id in seen_comment_ids:
                                    continue
                                if comment.score < MIN_COMMENT_SCORE:
                                    continue
                                if len(comment.body) < MIN_COMMENT_LENGTH:
                                    continue
                                seen_comment_ids.add(comment.id)
                                comment_url = f"{post.url}comment/{comment.id}/"
                                docs.append(
                                    Document(
                                        url=comment_url,
                                        title=f"Comment on: {post.title}",
                                        content=comment.body,
                                        source_type="reddit",
                                        metadata={
                                            "upvotes": comment.score,
                                            "reply_count": 0,
                                            "subreddit": subreddit_name,
                                            "post_id": post.id,
                                            "comment_id": comment.id,
                                        },
                                    )
                                )
                                count += 1
                        except Exception as e:
                            logger.warning(f"Failed to fetch comments for post {post.id}: {e}")

                except Exception as e:
                    logger.warning(f"Search failed for query '{query}' in r/{subreddit_name}: {e}")

        logger.info(f"RedditSource fetched {len(docs)} documents")
        return docs
