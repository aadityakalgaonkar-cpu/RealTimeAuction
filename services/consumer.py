import json
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Auctiontransaction, Auctionform

from asgiref.sync import sync_to_async


class myaswc(AsyncWebsocketConsumer):

    # shared memory for all auctions
    rooms = {}

    # ---------------- CONNECT ----------------

    async def connect(self):

        # getting auction id from websocket url
        self.auction_id = self.scope['url_route']['kwargs']['auction_id']

        # group name
        self.groupname = f"auction_{self.auction_id}"

        # add user to websocket group
        await self.channel_layer.group_add(

            self.groupname,
            self.channel_name

        )

        key = str(self.auction_id)

        # create room only once
        if key not in self.rooms:

            self.rooms[key] = {

                "highest_bid": 0,
                "highest_user": None,
                "timer": 30,
                "active": True

            }

            # start timer loop
            asyncio.create_task(
                self.timer_loop(self.auction_id)
            )

        await self.accept()

        # send current state to connected user
        state = self.rooms[key]

        await self.send(text_data=json.dumps({

            "type": "update",
            "bid": state["highest_bid"],
            "user": state["highest_user"],
            "timer": state["timer"],
            "active": state["active"]

        }))

    # ---------------- RECEIVE BID ----------------

    async def receive(self, text_data=None, bytes_data=None):

        key = str(self.auction_id)

        state = self.rooms[key]

        user = self.scope['user']

        try:

            data = json.loads(text_data)

            bidamount = int(data['bid'])

            # login check
            if not user.is_authenticated:

                await self.send(text_data=json.dumps({

                    "type": "error",
                    "message": "Login Required"

                }))

                return

            # auction ended check
            if not state["active"]:

                await self.send(text_data=json.dumps({

                    "type": "error",
                    "message": "Auction Ended"

                }))

                return

            # get auction
            auction = await sync_to_async(
                Auctionform.objects.get
            )(id=self.auction_id)

            # save every bid in database
            await sync_to_async(
                Auctiontransaction.objects.create
            )(

                auctionid=auction,
                userid=user,
                bidamount=bidamount

            )

            # update highest bid
            if bidamount > state["highest_bid"]:

                state["highest_bid"] = bidamount

                state["highest_user"] = user.username

                # reset timer
                state["timer"] = 30

            # send update to all users
            await self.channel_layer.group_send(

                self.groupname,

                {

                    "type": "send_update",
                    "data": state

                }

            )

        except Exception as e:

            await self.send(text_data=json.dumps({

                "type": "error",
                "message": str(e)

            }))

    # ---------------- SEND UPDATE ----------------

    async def send_update(self, event):

        data = event['data']

        await self.send(text_data=json.dumps({

            "type": "update",
            "bid": data["highest_bid"],
            "user": data["highest_user"],
            "timer": data["timer"],
            "active": data["active"]

        }))

    # ---------------- TIMER LOOP ----------------

    async def timer_loop(self, auction_id):

        key = str(auction_id)

        state = self.rooms[key]

        while state["active"]:

            await asyncio.sleep(1)

            state["timer"] -= 1

            # send timer updates
            await self.channel_layer.group_send(

                f"auction_{auction_id}",

                {

                    "type": "send_update",
                    "data": state

                }

            )

            # auction end
            if state["timer"] <= 0:

                state["active"] = False

                winner = state["highest_user"]

                final_bid = state["highest_bid"]

                # get auction object
                auction = await sync_to_async(
                    Auctionform.objects.get
                )(id=auction_id)

                # mark auction ended in db
                await sync_to_async(
                    Auctionform.objects.filter(id=auction_id).update
                )(
                    isactive=False
                )

                # mark winner in db
                if winner is not None:

                    await sync_to_async(
                        Auctiontransaction.objects.filter(
                            auctionid=auction,
                            userid__username=winner,
                            bidamount=final_bid
                        ).update
                    )(
                        winner=True
                    )

                # send final result
                await self.channel_layer.group_send(

                    f"auction_{auction_id}",

                    {

                        "type": "auction_end",
                        "winner": winner,
                        "bid": final_bid

                    }

                )

                # remove room from memory
                del self.rooms[key]

                break

    # ---------------- AUCTION END ----------------

    async def auction_end(self, event):

        await self.send(text_data=json.dumps({

            "type": "end",
            "winner": event["winner"],
            "bid": event["bid"]

        }))

    # ---------------- DISCONNECT ----------------

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(

            self.groupname,
            self.channel_name

        )